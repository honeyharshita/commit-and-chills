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

## Dashboard
The repository includes a local operations dashboard backed by the same decision and guardrail code.

```powershell
.venv\Scripts\activate
python -m precedent.web
```

Open http://localhost:8000. The dashboard runs the verified offline comparison by default and shows the
learning curve, auto-resolution lift, policy breaches, and recent invoice decisions.

The backend exposes `GET /api/health` and `POST /api/eval`. The dashboard is intentionally offline by
default so it remains useful without API credentials. The CLI is the path for the live Hindsight run.

## Local Hindsight
To use a self-hosted Hindsight container, set this in `.env`:

```env
HINDSIGHT_BASE_URL=http://localhost:8888
```

Keep `.env` local; it is excluded by `.gitignore`. Start Hindsight separately, then run the live CLI
evaluation. A reachable Hindsight server is not enough by itself: its configured LLM provider must also
be available to the account and model selected. If the provider rejects the request, the Hindsight arm
fails rather than silently producing fabricated results.

## Safety and limitations
- The offline dashboard uses `StubLLM` and `LocalMemory`, which are test doubles and must not be reported as live Hindsight results.
- The live evaluation requires a working Groq model and Hindsight backend; no live result is written when that run fails.
- Invoices above Rs 5,00,000 are escalated in code before memory or model output can authorize them.
- `.env`, `results.json`, and `learning_curve.png` are local or generated artifacts and are ignored by Git.

## Layout
`sim.py` synthetic stream + hidden ground-truth rules · `memory.py` Hindsight / baseline backends · `agent.py` decision + guardrails · `run.py` eval + CLI

`web.py` local HTTP backend · `web/index.html` dashboard markup · `web/app.js` dashboard behavior · `web/styles.css` dashboard styling
