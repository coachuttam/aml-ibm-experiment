"""Extra report sections: feature gain, the payment-format ablation, and the investigation summary."""

from __future__ import annotations

from typing import Dict, List

from src.ibm.case_text import typology_words
from src.ibm.train import ModelScores, gain_importance

ABLATION_NAME = "LightGBM − payment format"


def gain_table_rows(model) -> List[List[str]]:
    """Feature, total gain and share of all gain, largest first."""
    pairs = gain_importance(model)
    total = sum(gain for _, gain in pairs) or 1.0
    return [[name, "%.0f" % gain, "%.1f%%" % (100 * gain / total)] for name, gain in pairs]


def ablation_row(scores: ModelScores) -> List[str]:
    """The ablation's test result in the Overall table's columns."""
    return [
        ABLATION_NAME,
        str(scores.alerts),
        "%.4f" % scores.precision,
        "%.3f" % scores.recall,
        "%.3f" % scores.minority_f1,
        "%.3f" % scores.pr_auc,
        "%.2f" % scores.precision_at_100,
    ]


def investigation_lines(investigation: Dict[str, object]) -> List[str]:
    """Plain-English summary of the top-alert investigations and the typology score."""
    top, wide = investigation["top_accuracy"], investigation["test_accuracy"]
    records = investigation["records"]
    guesses = sorted({typology_words(record["typology"]) for record in records})
    return [
        "- Investigated the %d highest-scored test alerts; %d of them are truly laundering."
        % (len(records), investigation["top_really_laundering"]),
        "- Typology accuracy against the patterns file on those alerts: %d of %d (%.0f%%)."
        % (top["correct"], top["rows"], 100 * top["accuracy"]),
        "- Same classifier on every test-period laundering row with a listed typology: %d of %d (%.0f%%)."
        % (wide["correct"], wide["rows"], 100 * wide["accuracy"]),
        "- Typologies suggested: %s." % ", ".join(guesses),
        "- The typology classifier is a LightGBM model trained on training-period laundering rows only. "
        "Each investigation is saved in `results/ibm_investigations.jsonl`; nothing is filed or sent.",
    ]
