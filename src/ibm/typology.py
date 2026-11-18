"""Suggest which laundering typology an alert looks like, from its counted evidence.

A small LightGBM classifier learns this from the laundering rows of the training
period only (labels come from the patterns file). It labels; the numbers it reads
are counted by Python in evidence.py. Rows the patterns file does not describe
(UNLISTED) are left out, because they have no typology to learn.

Example:
    classifier = train_typology_classifier(evidence_list, typology_names)
    name = predict_typology(classifier, evidence)
"""

from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from src.ibm.evidence import NUMBER_NAMES, Evidence

TREES = 150
LEAVES = 7  # small: only a couple of thousand training rows
RANDOM_SEED = 42
MIN_TRAINING_ROWS = 2  # a classifier needs at least two examples to fit anything


def evidence_table(evidence_list: List[Evidence]) -> pd.DataFrame:
    """One row per alert, one column per counted number."""
    return pd.DataFrame([item.numbers for item in evidence_list], columns=NUMBER_NAMES)


def train_typology_classifier(evidence_list: List[Evidence], typologies: List[str]):
    """Fit the multi-class model. Returns None when there is too little data to learn from."""
    if len(set(typologies)) < MIN_TRAINING_ROWS:
        return None
    import lightgbm

    model = lightgbm.LGBMClassifier(
        n_estimators=TREES,
        num_leaves=LEAVES,
        learning_rate=0.05,
        min_child_samples=5,
        random_state=RANDOM_SEED,
        verbose=-1,
    )
    model.fit(evidence_table(evidence_list), np.array(typologies))
    return model


def predict_typologies(classifier, evidence_list: List[Evidence], fallback: str = "UNKNOWN") -> List[str]:
    """The most likely typology for each alert, or `fallback` when there is no classifier."""
    if classifier is None or not evidence_list:
        return [fallback] * len(evidence_list)
    return [str(name) for name in classifier.predict(evidence_table(evidence_list))]
