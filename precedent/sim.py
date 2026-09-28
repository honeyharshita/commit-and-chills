"""Synthetic AP exception stream + the company's *unwritten* rules (ground truth).

The agent is never shown these rules. It can only learn them from reviewer
resolutions that get retained in memory. That is what makes memory measurable.
"""
from __future__ import annotations
import random
from dataclasses import dataclass
from datetime import datetime, timedelta

VENDORS = ["Sunrise Logistics", "Deccan Office Supplies", "Nizam Facility Services",
           "Charminar Print & Pack", "Hussain Sagar Catering", "Golconda Tech Parts",
           "Kaveri Cloud Services"]
QUIRK = {"Sunrise Logistics": "FREIGHT_NOT_ON_PO", "Deccan Office Supplies": "PRICE_VARIANCE",
         "Nizam Facility Services": "DUPLICATE_REISSUE", "Charminar Print & Pack": "MISSING_GRN",
         "Hussain Sagar Catering": "TDS_MISMATCH"}
EXCEPTIONS = ["FREIGHT_NOT_ON_PO", "PRICE_VARIANCE", "DUPLICATE_REISSUE", "MISSING_GRN", "TDS_MISMATCH"]
HARD_LIMIT = 500_000      # written policy: above this, a human always signs
DRIFT_FRACTION = 0.6      # Deccan's contract changes 60% of the way through the stream

@dataclass
class Invoice:
    id: str
    vendor: str
    exc: str
    amount: int
    pct: float
    date: datetime

    @property
    def erp_note(self) -> str:
        return {
            "FREIGHT_NOT_ON_PO": f"3-way match failed: freight line = {self.pct}% of invoice value, not on PO",
            "PRICE_VARIANCE": f"3-way match failed: unit price {self.pct}% above PO price",
            "DUPLICATE_REISSUE": f"invoice number {self.id}-R resembles already-paid invoice {self.id}",
            "MISSING_GRN": "3-way match failed: no goods receipt posted against PO",
            "TDS_MISMATCH": "TDS deducted at 2% on invoice; vendor master says 1%",
        }[self.exc]

def make_stream(n: int = 150, seed: int = 7) -> list[Invoice]:
    rng, day, out = random.Random(seed), datetime(2026, 4, 1, 9), []
    for i in range(n):
        v = rng.choice(VENDORS)
        e = QUIRK[v] if v in QUIRK and rng.random() < 0.7 else rng.choice(EXCEPTIONS)
        pct = {"FREIGHT_NOT_ON_PO": rng.choice([3, 5, 6, 7, 9, 12]),
               "PRICE_VARIANCE": rng.choice([0.5, 1, 1.5, 2, 3.5, 5])}.get(e, 0)
        amt = rng.randint(520_000, 900_000) if rng.random() < 0.06 else rng.randint(20_000, 480_000)
        day += timedelta(hours=rng.randint(8, 30))
        out.append(Invoice(f"INV-{1000 + i}", v, e, round(amt, -1), pct, day))
    return out

def truth(inv: Invoice, step: int, n: int) -> tuple[str, str]:
    """Return (correct_action, the reviewer's stated reason)."""
    if inv.amount > HARD_LIMIT:
        return "ESCALATE", "Policy: anything above Rs 5,00,000 needs controller sign-off, no exceptions."
    v, e, p = inv.vendor, inv.exc, inv.pct
    if v == "Sunrise Logistics" and e == "FREIGHT_NOT_ON_PO":
        return (("APPROVE", "Sunrise freight is billed outside the PO by contract; controller allows up to 8%.")
                if p <= 8 else ("ESCALATE", "Sunrise freight above the 8% cap needs controller review."))
    if v == "Deccan Office Supplies" and e == "PRICE_VARIANCE":
        if step >= int(n * DRIFT_FRACTION):
            return "HOLD", "New Deccan contract: zero price tolerance. Hold and request a credit note."
        return (("APPROVE", "Deccan price variance up to 2% is tolerated under the old contract.")
                if p <= 2 else ("ESCALATE", "Deccan variance above 2% needs controller review."))
    if v == "Nizam Facility Services" and e == "DUPLICATE_REISSUE":
        return "REJECT", "Nizam re-issues invoices with an -R suffix; the original was paid. Reject the duplicate."
    if v == "Charminar Print & Pack" and e == "MISSING_GRN":
        return "HOLD", "Charminar warehouse posts receipts late; hold until the GRN appears."
    if v == "Hussain Sagar Catering" and e == "TDS_MISMATCH":
        return "APPROVE", "Catering TDS rate is corrected by AP internally; approve."
    return "ESCALATE", "No standing rule for this vendor and exception; controller decides."
