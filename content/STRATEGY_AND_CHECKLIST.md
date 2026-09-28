# Why this project, and how to submit it

## Idea selection (weighed against the judging rubric)
| Candidate | Problem | Verdict |
|---|---|---|
| Deal intelligence / sales | Hundreds of teams will build it; judges will see 30 near-identical demos | Drop |
| Customer support | Same crowding; "remembers the customer" is the obvious pitch | Drop |
| Incident response / code review | Popular with engineers, hard to show a *measurable* before/after in 60 s | Drop |
| Compliance & audit | Strong, but hard to generate realistic data quickly | Backup |
| **Accounts payable exceptions** | Under-built, clear ROI (each exception is a human touch), rules are truly tribal knowledge | **Chosen** |

**Differentiators**
- **Innovation (30%)**: policy drift (a vendor's contract changes mid-stream) and "memory must not override policy" are rarely shown.
- **Memory (25%)**: built-in A/B harness produces a learning curve; no hand-waving.
- **Technical (20%)**: guardrails, fail-safe, citation requirement, deterministic seed, retries for LLM errors.
- **UX (15%)**: `brief` command answers in one line; the demo story is 60 seconds.
- **Impact (10%)**: AP automation is a real budget line; ties to human-touch reduction.

## Be honest with yourself before submitting
- I could not run Hindsight or Groq from my sandbox (no network). The code matches the documented v0.10 API, but **run it once and fix anything small** before recording.
- **Do not publish numbers you did not measure.** The article has three `[[...]]` slots; fill them from your own `results.json`.
- Nobody can guarantee selection among thousands of entries. What you control: working demo, measured result, clear story.

## 60-minute plan
1. (10 min) Create Hindsight Cloud account, add promo `MEMHACK99` in billing, set `.env`, run `eval --n 30` to check.
2. (10 min) Full `eval --n 150`; save `learning_curve.png` and terminal screenshots.
3. (15 min) Fill slots in `article.md`, add screenshots, publish on Dev.to/Medium/Hashnode. **Never write the word "hackathon" anywhere**, including hashtags.
4. (5 min) Post `linkedin_post.txt` with repo link; article URL as first comment; Hindsight repo link as a second comment; tag Code.in.
5. (5 min) Submit the article to r/llmdevs, r/aiagents, r/aimemory or r/sideproject as a *Link* post.
6. (15 min) Record video from `video_script.md`, make thumbnail, upload public to YouTube.

## Pre-submit checklist
- [ ] Repo public, README renders, `.env` NOT committed
- [ ] Article public, 3 Hindsight links live, screenshots added, no "hackathon" text
- [ ] LinkedIn post live; repo link in body; article + Hindsight links in comments; Code.in tagged
- [ ] Reddit link post done
- [ ] Video public on YouTube with custom thumbnail
- [ ] Every team member has their own article + post (edit angles: one on guardrails, one on drift, one on eval harness)
