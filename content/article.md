# Hindsight Taught My AP Agent Rules Nobody Wrote Down

The most expensive sentence in accounts payable is "just ask the controller." Our agent asked the controller about every failed invoice match, including ones the controller had answered the same way forty times.

I built **Precedent**, an exception-handling agent for accounts payable, to fix that. The interesting part isn't the LLM. It's what happens when you give it [Hindsight agent memory](https://vectorize.io/what-is-agent-memory) and then change the rules underneath it.

## The problem: rules that live in people's heads

When an invoice fails a three-way match against the PO and goods receipt, a person decides what to do. Over time they build vendor-specific habits:

- Sunrise Logistics bills freight outside the PO. Approve up to 8%.
- Nizam Facility Services re-issues invoices with an `-R` suffix. Reject the duplicate.
- Charminar Print & Pack posts goods receipts late. Hold, don't escalate.

None of this is in the ERP. A stateless agent can't know it, so it does the only safe thing: escalate everything. Safe, and useless.

## How it hangs together

Each invoice goes through four steps:

1. `recall` precedent for this vendor and exception from Hindsight.
2. The LLM (Groq, `gpt-oss-120b`) picks `APPROVE`, `REJECT`, `HOLD` or `ESCALATE`, and must cite a precedent.
3. Guardrails in code check the answer.
4. If a human was involved (escalation, or a correction of a wrong auto-decision), that resolution is `retain`ed as a dated memory.

Retention is just a reviewer note in plain language, with the invoice date as the timestamp:

```python
self.c.retain(bank_id=self.bank, content=content, context=context,
              timestamp=when, retain_async=False)
```

Recall pulls semantic, keyword, entity-graph and temporal matches, so "Sunrise freight 7%" finds the right notes even when the wording differs:

```python
r = self.c.recall(bank_id=self.bank, query=query,
                  types=["world", "experience", "observation"],
                  budget="mid", max_tokens=1500)
```

## The through-line: memory must not outrank policy

The first version trusted precedent too much. If a controller approved a large invoice once, the agent happily learned "large is fine." That's how memory turns into a compliance incident.

So the hard limit lives in code, before the model is called:

```python
if inv.amount > HARD_LIMIT:
    return Decision("ESCALATE", "Above policy limit; human sign-off required.", [], False)
```

Two more rules came from the same lesson. Any non-escalation action must cite a recalled precedent, otherwise it's forced back to `ESCALATE`. And unparseable model output escalates rather than guessing. Memory makes the agent more autonomous; these rules keep that autonomy earned rather than assumed.

I also built decoy vendors with no standing rules. If the agent starts approving their exceptions because a *different* vendor's precedent looked similar, that shows up as a wrong auto-resolution in the eval.

## The part I didn't expect: rules change

Halfway through my replay, Deccan Office Supplies' contract changes. Price variance up to 2% used to be fine. Now it's zero tolerance: hold and ask for a credit note.

An agent with a static rulebook keeps approving. An agent with an append-only pile of notes sees conflicting precedent and has to guess. Hindsight consolidates related facts into observations and updates them as new evidence arrives, keeping history rather than overwriting it. My prompt says the most recent precedent wins, and the retained corrections ("Agent had proposed APPROVE; reviewer corrected it") give it exactly the evidence to switch.

In the eval this shows up as a dip in the learning curve right after the contract change, followed by recovery as corrected precedent accumulates.

## Results

I replay the same 150-invoice stream through two arms with identical prompts and ERP data: no memory, and Hindsight. The harness writes `results.json` and a learning curve.

- No memory: **[[X]]** of 150 invoices resolved without a human.
- Hindsight: **[[Y]]** of 150 resolved without a human, with **[[Z]]** wrong auto-resolutions and **0** policy breaches.

The `brief` command shows the same memory through `reflect`:

```
$ python -m precedent.run brief --vendor "Deccan Office Supplies" --bank <bank>
```

Ask it about Deccan and it answers with the old 2% tolerance, the date the contract changed, and the new hold-and-credit-note rule.

## What I'd tell another engineer

1. **Write the eval before the agent.** A seeded stream with hidden ground-truth rules made every claim testable.
2. **Guardrails go in code, not the prompt.** The limit check runs before the model.
3. **Make autonomy cite its source.** "No citation, no action" cut confident wrong answers more than any prompt tweak.
4. **Test memory against change, not just recall.** Remembering is easy. Updating is the hard part.
5. **Timestamp everything.** Passing the invoice date to `retain` is what lets recency matter.

The code is on GitHub: https://github.com/honeyharshita/commit-and-chill. To try the memory layer yourself, start with the [Hindsight GitHub repository](https://github.com/vectorize-io/hindsight) and the [Hindsight documentation](https://hindsight.vectorize.io/).
