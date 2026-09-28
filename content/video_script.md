# Video script (about 3 min) + titles

Record at 1080p. Big terminal font. Don't read verbatim.

**0:00 Intro (30s)** — On camera, then screen: README.
"Hi, I'm [NAME]. Finance teams have rules that live in someone's head, like 'approve Sunrise freight up to 8%.' I built Precedent, an accounts-payable agent that learns those rules using Hindsight memory, so it stops asking the controller the same question."

**0:30 The problem (30s)** — Screen: `python -m precedent.run eval --arms none --n 30`
"Here's the same agent with no memory. Every failed invoice match: escalate. Zero auto-resolved. It's safe, but it saves nobody any time."

**1:00 Demo (2 min)** — Screen: `eval --arms none,hindsight --n 150`, then open `learning_curve.png`.
- "Same 150 invoices, same prompts, same ERP data. One arm has Hindsight." Point at the table: windows 1–25 vs 126–150.
- Show `agent.py` guardrail: "Over Rs 5 lakh escalates in code. Memory can't override policy."
- Show `memory.py` retain/recall lines: "Every reviewer note is retained with the invoice date."
- Point at the dip: "Here Deccan's contract changed to zero tolerance. The agent approved a stale rule, got corrected, and recovered."
- Run `brief --vendor "Deccan Office Supplies"`: "Reflect gives me the old rule, the change, and the new rule."

**2:30 Takeaway (30s)** — Back on camera.
"What surprised me: remembering was easy. Updating was the real test. And putting guardrails in code, not the prompt, is what makes this something a finance team could trust. Repo's linked below."

## Titles
1. My AP Agent Kept Approving Invoices After the Contract Changed
2. I Gave an AI Agent Memory and It Stopped Bothering the Controller
3. Hindsight Memory vs No Memory: 150 Invoices, Same Agent
4. Why My Finance Agent Can't Override Policy (Even With Memory)
5. The AI Agent That Learns Unwritten Company Rules

## Thumbnail prompt (Nano Banana, attach a team photo, 16:9)
Generate a viral 16:9 YouTube thumbnail. Left: the attached person looking surprised, pointing at the right. Right: a split screen, red "ESCALATE ×150" stacked on top of a green "AUTO-RESOLVED" learning curve rising. Big bold text: "IT LEARNED THE RULES". Dark background, high contrast, yellow accent, no small text, no logos.
