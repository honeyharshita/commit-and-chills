# Precedent — an accounts-payable agent that learns your unwritten rules

Every finance team has rules that live in someone's head: *"Sunrise's freight is never on the PO, approve up to 8%."*
*"Nizam re-issues invoices with an -R suffix, reject those."* Stateless agents escalate everything to the controller.
**Precedent** remembers how humans resolved each vendor's exceptions, using [Hindsight](https://github.com/vectorize-io/hindsight) agent memory,
and quietly stops asking the same question twice.

## Why memory is the product
| Hindsight feature | How Precedent uses it |
|---|---|
| `retain` (with `timestamp`) | Every reviewer resolution becomes a dated memory; corrections to the agent's mistakes are retained too |
| `recall` (semantic + keyword + graph + temporal) | Pulls vendor-specific precedent before each decision |
| Observations / consolidation | When Deccan's contract changes, newer evidence supersedes the old rule instead of piling up beside it |
| `reflect` + bank `mission` | `brief` command: "how do we handle Deccan, and what changed recently?" |

## Safety design (why a CFO could trust it)
1. **Memory can't override policy.** Invoices over Rs 5,00,000 escalate in code, before the LLM is called.
2. **No citation, no autonomy.** Any non-ESCALATE action must cite a recalled precedent, otherwise it's forced to ESCALATE.
3. **Fail safe.** Unparseable model output escalates.
4. **No cross-vendor leakage.** Decoy vendors (Golconda, Kaveri) have no rules; the agent must not borrow other vendors' precedent.

## Run it
```bash
pip install -r requirements.txt && cp .env.example .env   # add HINDSIGHT + GROQ keys
python -m precedent.run eval --arms none,hindsight --n 150   # A/B: same agent, with vs without memory
python -m precedent.run brief --vendor "Deccan Office Supplies" --bank <bank id printed by eval>
```
`eval` replays 150 invoices twice (baseline vs Hindsight), writes `results.json` and `learning_curve.png`.
Mid-stream, Deccan's contract changes (2% tolerance → zero), so you can see the dip and recovery.
`--llm stub --arms none,local` runs fully offline as a smoke test; those numbers are test-double output, not results.

## Layout
`sim.py` synthetic stream + hidden ground-truth rules · `memory.py` Hindsight / baseline backends · `agent.py` decision + guardrails · `run.py` eval + CLI
