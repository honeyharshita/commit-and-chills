from __future__ import annotations
import os, re
from datetime import datetime

MISSION = ("I am the accounts-payable exception analyst for a mid-size company. I remember how the "
           "controller and AP reviewers resolved each vendor's invoice exceptions, including when a "
           "vendor's terms change. Recent reviewer decisions override older ones. Precedent for one "
           "vendor or exception type never applies to another.")

class Memory:
    name = "none"
    def recall(self, query: str) -> list[str]: return []
    def retain(self, content: str, when: datetime, context: str) -> None: pass
    def brief(self, vendor: str) -> str: return "(no memory backend)"

class NoMemory(Memory):
    """Baseline: same agent, same ERP data, zero memory."""

class HindsightMemory(Memory):
    name = "hindsight"
    def __init__(self, bank_id: str):
        from hindsight_client import Hindsight
        kw = {"base_url": os.environ.get("HINDSIGHT_BASE_URL", "http://localhost:8888"), "timeout": 120.0}
        if os.environ.get("HINDSIGHT_API_KEY"):
            kw["api_key"] = os.environ["HINDSIGHT_API_KEY"]
        self.c, self.bank = Hindsight(**kw), bank_id
        self.c.create_bank(bank_id=bank_id, name="Precedent AP", mission=MISSION)

    def recall(self, query: str) -> list[str]:
        r = self.c.recall(bank_id=self.bank, query=query, types=["world", "experience", "observation"],
                          budget="mid", max_tokens=1500)
        return [f"[{x.type}] {x.text}" for x in r.results]

    def retain(self, content: str, when: datetime, context: str) -> None:
        self.c.retain(bank_id=self.bank, content=content, context=context, timestamp=when, retain_async=False)

    def brief(self, vendor: str) -> str:
        q = (f"Brief me on how we handle invoice exceptions from {vendor}. "
             "What is the standing rule, and has anything changed recently?")
        return self.c.reflect(bank_id=self.bank, query=q, budget="mid").text

class LocalMemory(Memory):
    """OFFLINE TEST DOUBLE (keyword overlap). Only for CI/smoke tests, never for reported results."""
    name = "local-test-double"
    def __init__(self): self.items: list[tuple[datetime, str]] = []
    def retain(self, content, when, context): self.items.append((when, content))
    def recall(self, query):
        q = set(re.findall(r"\w+", query.lower()))
        scored = sorted(self.items, key=lambda t: (len(q & set(re.findall(r"\w+", t[1].lower()))), t[0]), reverse=True)
        return [f"[experience] {t[1]}" for t in scored[:8]]
