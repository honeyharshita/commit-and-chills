from __future__ import annotations
import argparse, json, time
from dotenv import load_dotenv
from .sim import make_stream, truth, Invoice
from .memory import NoMemory, HindsightMemory, LocalMemory
from .agent import decide, GroqLLM, StubLLM

def note(inv: Invoice, action: str, why: str, agent_action: str) -> str:
    fix = f" (Agent had proposed {agent_action}; reviewer corrected it.)" if agent_action not in ("ESCALATE", action) else ""
    return (f"Reviewer note {inv.date:%Y-%m-%d}: vendor {inv.vendor}, invoice {inv.id}, exception {inv.exc} "
            f"({inv.pct}%), amount Rs {inv.amount:,}. Resolution: {action}. {why}{fix}")

def run_arm(mem, llm, stream, window=25):
    rows, n = [], len(stream)
    for i, inv in enumerate(stream):
        pre = mem.recall(f"{inv.vendor} {inv.exc} {inv.erp_note} invoice exception resolution")
        d = decide(llm, inv, pre)
        want, why = truth(inv, i, n)
        auto, ok = d.action != "ESCALATE", d.action == want
        if not auto or not ok:            # a human touched it -> that resolution becomes memory
            mem.retain(note(inv, want, why, d.action), inv.date, "AP exception resolution")
        else:                             # confirmed precedent
            mem.retain(f"Auto-resolved {inv.date:%Y-%m-%d}: {inv.vendor} {inv.exc} ({inv.pct}%) -> {d.action}; "
                       f"no reviewer objection.", inv.date, "AP auto-resolution")
        rows.append({"i": i, "vendor": inv.vendor, "exc": inv.exc, "agent": d.action, "truth": want,
                     "auto": auto, "auto_correct": auto and ok, "auto_wrong": auto and not ok,
                     "over_limit_auto": inv.amount > 500_000 and auto})
        if (i + 1) % 10 == 0: print(f"  [{mem.name}] {i + 1}/{n}", flush=True)
    wins = []
    for s in range(0, n, window):
        w = rows[s:s + window]
        wins.append({"window": f"{s + 1}-{s + len(w)}", "auto_correct_pct": round(100 * sum(r["auto_correct"] for r in w) / len(w), 1),
                     "wrong_auto": sum(r["auto_wrong"] for r in w)})
    return rows, wins

def cmd_eval(a):
    stream = make_stream(a.n, a.seed)
    llm = StubLLM() if a.llm == "stub" else GroqLLM()
    bank = a.bank or f"precedent-{int(time.time())}"
    mk = {"none": NoMemory, "local": LocalMemory, "hindsight": lambda: HindsightMemory(bank)}
    out = {}
    for arm in a.arms.split(","):
        print(f"== arm: {arm}")
        rows, wins = run_arm(mk[arm](), llm, stream)
        out[arm] = {"windows": wins, "over_limit_auto": sum(r["over_limit_auto"] for r in rows),
                    "total_auto_correct": sum(r["auto_correct"] for r in rows),
                    "total_auto_wrong": sum(r["auto_wrong"] for r in rows), "n": len(rows)}
    print("\nAuto-resolved correctly, % of invoices per window (wrong auto-resolutions in brackets)")
    print(f"{'window':>10} " + " ".join(f"{k:>16}" for k in out))
    for j, w in enumerate(next(iter(out.values()))["windows"]):
        print(f"{w['window']:>10} " + " ".join(f"{out[k]['windows'][j]['auto_correct_pct']:>9}% ({out[k]['windows'][j]['wrong_auto']})" for k in out))
    for k, v in out.items():
        print(f"{k}: {v['total_auto_correct']}/{v['n']} auto-correct, {v['total_auto_wrong']} wrong, policy breaches: {v['over_limit_auto']}")
    json.dump({"bank_id": bank, "results": out}, open("results.json", "w"), indent=2)
    print(f"\nSaved results.json  (Hindsight bank: {bank})")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        for k, v in out.items(): plt.plot([w["window"] for w in v["windows"]], [w["auto_correct_pct"] for w in v["windows"]], marker="o", label=k)
        plt.ylabel("% invoices auto-resolved correctly"); plt.xlabel("invoice window"); plt.legend(); plt.grid(alpha=.3)
        plt.savefig("learning_curve.png", dpi=160, bbox_inches="tight"); print("Saved learning_curve.png")
    except Exception: pass

def _brief(a):
    m = HindsightMemory(a.bank)   # create_bank on an existing bank id is an update, not a reset
    return m.brief(a.vendor)

def main():
    load_dotenv()
    p = argparse.ArgumentParser(prog="precedent")
    s = p.add_subparsers(dest="cmd", required=True)
    e = s.add_parser("eval"); e.add_argument("--n", type=int, default=150); e.add_argument("--seed", type=int, default=7)
    e.add_argument("--arms", default="none,hindsight"); e.add_argument("--llm", choices=["groq", "stub"], default="groq")
    e.add_argument("--bank"); e.set_defaults(f=cmd_eval)
    b = s.add_parser("brief"); b.add_argument("--vendor", required=True); b.add_argument("--bank", required=True)
    b.set_defaults(f=lambda a: print(_brief(a)))
    a = p.parse_args(); a.f(a)

if __name__ == "__main__":
    main()
