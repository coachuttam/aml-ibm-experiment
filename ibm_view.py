"""The "IBM alerts" tab: the model's top IBM AML alerts, with evidence, case note and draft report.

Reads the saved investigations in results/ibm_investigations.jsonl (made by
`python -m src.ibm.compare`), so the app never loads the 5-million-row file.
Nothing here files or sends anything.
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd
import streamlit as st

from evidence_view import show_table
from src.ibm.case_text import typology_words
from src.ibm.investigate import load_records

STEP_MARKS = {
    "done": "✔ done",
    "needs_review": "⚠ needs review",
    "unavailable": "– not available",
    "waiting": "… waiting for the analyst",
}


def alert_table(records: List[Dict[str, object]]) -> pd.DataFrame:
    """One row per alert for the list."""
    return pd.DataFrame(
        [
            {
                "Alert": r["alert_id"],
                "Time": r["time"],
                "Score": round(r["score"], 3),
                "Suggested typology": typology_words(r["typology"]),
                "Patterns file says": typology_words(r["true_typology"])
                if r["true_typology"] != "NONE"
                else "not laundering",
                "Amount": "%.2f %s" % (r["amount"], r["currency"]),
            }
            for r in records
        ]
    )


def show_evidence_rows(record: Dict[str, object]) -> None:
    """Findings, then the sender's and receiver's recent transactions."""
    for finding in record["findings"]:
        st.markdown("- " + finding)
    left, right = st.columns(2)
    with left:
        st.caption("Sender: latest payments sent in the 7 days up to the alert")
        show_table(pd.DataFrame(record["sender_rows"]))
    with right:
        st.caption("Receiver: latest payments received in the 7 days up to the alert")
        show_table(pd.DataFrame(record["receiver_rows"]))


def show_steps(record: Dict[str, object]) -> None:
    for step in record["steps"]:
        mark = STEP_MARKS.get(step["status"], step["status"])
        st.markdown("**%d. %s** · %s · %s" % (step["number"], step["name"], mark, step["summary"]))


def show_ibm_alerts() -> None:
    records = load_records()
    if not records:
        st.info(
            "No IBM investigations yet. Run `python -m src.ibm.compare` to make them "
            "(needs data/HI-Small_Trans.csv and data/HI-Small_Patterns.txt)."
        )
        return
    st.caption(
        "The 20 highest-scored test-period alerts from the LightGBM model on the public IBM AML data. "
        "Python counted every number. Nothing has been filed or sent."
    )
    show_table(alert_table(records))
    chosen = st.selectbox("Open an alert", [r["alert_id"] for r in records], key="ibm_alert_choice")
    record = next(r for r in records if r["alert_id"] == chosen)
    evidence_tab, note_tab, report_tab, steps_tab = st.tabs(["Evidence", "Case note", "Draft report", "Steps"])
    with evidence_tab:
        show_evidence_rows(record)
    with note_tab:
        st.markdown(record["case_note"])
    with report_tab:
        st.markdown(record["report"])
    with steps_tab:
        show_steps(record)
