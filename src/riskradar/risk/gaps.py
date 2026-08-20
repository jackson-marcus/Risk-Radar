"""Rule-based diligence gaps: vendor attributes vs policy requirements.

Each gap cites a rule_id from docs/diligence.md — the same corpus the RAG
assistant serves — so every finding is grounded in written policy.
"""

from __future__ import annotations

import pandas as pd


def diligence_gaps(vendor: dict, events: pd.DataFrame) -> list[dict]:
    gaps = []
    if vendor["handles_pii"] and not vendor["has_soc2"]:
        gaps.append(
            {"rule_id": "security-soc2", "finding": "Handles PII without a current SOC 2 report."}
        )
        gaps.append(
            {"rule_id": "pii-dpa", "finding": "PII processing requires an executed DPA on file."}
        )
    if vendor["single_source"] and vendor["annual_spend_usd"] > 400_000:
        gaps.append(
            {
                "rule_id": "concentration-limit",
                "finding": f"Single-sourced at ${vendor['annual_spend_usd']:,}/yr — exceeds concentration policy.",
            }
        )
        gaps.append(
            {
                "rule_id": "exit-plan",
                "finding": "No documented exit plan for a single-source dependency.",
            }
        )
    security_events = events[(events["category"] == "security")]
    if len(security_events) >= 3:
        gaps.append(
            {
                "rule_id": "incident-notification",
                "finding": f"{len(security_events)} security events on record — verify notification clause.",
            }
        )
    if vendor["years_active"] < 2:
        gaps.append(
            {
                "rule_id": "financial-review",
                "finding": "Vendor younger than 2 years: enhanced financial review required.",
            }
        )
    return gaps
