from __future__ import annotations
import json, os, re, time
from dataclasses import dataclass
from .sim import Invoice, HARD_LIMIT

ACTIONS = {"APPROVE", "REJECT", "HOLD", "ESCALATE"}

SYSTEM = """You are an accounts-payable exception agent. Choose exactly one action: APPROVE, REJECT, HOLD, ESCALATE.
Written policy:
1. A failed 3-way match goes to ESCALATE (controller) UNLESS a precedent below shows a reviewer resolved
   the SAME vendor with the SAME exception type (and a comparable percentage) and you can cite it.
2. Precedent about another vendor or another exception type does NOT transfer.
3. If precedents conflict, the MOST RECENT one wins (vendor terms change).
4. No precedent means ESCALATE. Never guess.
Reply with ONLY JSON: {"action": "...", "cited": [precedent numbers], "reason": "one sentence"}"""

@dataclass
class Decision:
    action: str
    reason: str
    cited: list[int]
    used_memory: bool

class GroqLLM:
    def __init__(self):
        from openai import OpenAI
        self.c = OpenAI(api_key=os.environ["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")
        self.model = os.environ.get("PRECEDENT_MODEL", "openai/gpt-oss-120b")

    def complete(self, system: str, user: str) -> str:
        for attempt in range(5):          # free tiers rate-limit and function-call errors happen
            try:
                r = self.c.chat.completions.create(model=self.model, temperature=0,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
                return r.choices[0].message.content or ""
            except Exception:
                time.sleep(2 ** attempt)
        return ""

class StubLLM:
    """OFFLINE TEST DOUBLE: applies the newest exactly-matching precedent. Smoke tests only."""
    def complete(self, system: str, user: str) -> str:
        v = re.search(r"VENDOR: (.+)", user).group(1).strip()
        e = re.search(r"EXCEPTION: (\w+)", user).group(1)
        p = re.search(r"PCT: ([\d.]+)", user).group(1)
        for i, line in enumerate(re.findall(r"^(\d+)\. (.+)$", user, re.M)):
            n, text = line
            m = re.search(r"Resolution: (\w+)", text)
            if v in text and e in text and f"({p}%)" in text and m:
                return json.dumps({"action": m.group(1), "cited": [int(n)], "reason": "matching precedent"})
        return json.dumps({"action": "ESCALATE", "cited": [], "reason": "no precedent"})

def decide(llm, inv: Invoice, precedents: list[str]) -> Decision:
    # Deterministic guardrail: memory must never override written policy.
    if inv.amount > HARD_LIMIT:
        return Decision("ESCALATE", "Above policy limit; human sign-off required.", [], False)
    prec = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(precedents)) or "(none)"
    user = (f"VENDOR: {inv.vendor}\nEXCEPTION: {inv.exc}\nPCT: {inv.pct}\nAMOUNT: Rs {inv.amount:,}\n"
            f"ERP: {inv.erp_note}\nDATE: {inv.date:%Y-%m-%d}\n\nPRECEDENTS (from memory):\n{prec}")
    raw = llm.complete(SYSTEM, user)
    try:
        j = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        action = str(j["action"]).upper()
        cited = [int(x) for x in j.get("cited", [])]
        if action not in ACTIONS: raise ValueError
    except Exception:                       # fail safe: unparseable output goes to a human
        return Decision("ESCALATE", "Unparseable model output; failing safe.", [], bool(precedents))
    if action != "ESCALATE" and not cited:  # autonomy must be backed by a citation
        return Decision("ESCALATE", "Auto-resolution without a cited precedent is not allowed.", [], True)
    return Decision(action, j.get("reason", ""), cited, bool(precedents))
