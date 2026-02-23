"""
Production-safer ML scoring wrapper for your native XGBoost model.

Why this exists
- Your model file is a *native XGBoost Booster* (JSON).
- Your metadata explicitly says preprocessing (one-hot, imputers) is NOT included.
- Therefore, this wrapper enforces:
  1) exact feature set (no missing/extra),
  2) exact feature ordering (from metadata),
  3) numeric-only inputs (until you plug in a preprocessing pipeline),
  4) stable, explicit outputs (CI class + probabilities).

Expected inputs
- A dict keyed by the feature names listed in metadata["feature_columns_before_preprocess"]
  (e.g., registry, project_type, methodology, country, ...)
- Values must be numeric (int/float). If you have strings (e.g., "Verra"),
  you must map/encode them before scoring, or provide the joblib preprocessing pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import json
import math

import numpy as np
import xgboost as xgb


class FeatureValidationError(ValueError):
    """Raised when feature schema/order/types are invalid for scoring."""


@dataclass(frozen=True)
class ModelSchema:
    label_classes: List[str]
    feature_columns_before_preprocess: List[str]
    version: Optional[str] = None
    notes: Optional[str] = None


def _load_schema(metadata_path: str) -> ModelSchema:
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    label_classes = meta.get("label_classes")
    feature_cols = meta.get("feature_columns_before_preprocess")

    if not isinstance(label_classes, list) or not all(isinstance(x, str) for x in label_classes):
        raise FeatureValidationError("metadata['label_classes'] must be a list of strings.")
    if not isinstance(feature_cols, list) or not all(isinstance(x, str) for x in feature_cols):
        raise FeatureValidationError("metadata['feature_columns_before_preprocess'] must be a list of strings.")

    return ModelSchema(
        label_classes=label_classes,
        feature_columns_before_preprocess=feature_cols,
        version=meta.get("version"),
        notes=meta.get("notes"),
    )


def _is_number(x: Any) -> bool:
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return not (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))
    return False


class MLScoringService:
    """
    Wraps an XGBoost Booster (native model) + metadata schema.
    """
    def __init__(self, model_path: str, metadata_path: str):
        self.model_path = model_path
        self.metadata_path = metadata_path

        # Load model
        self.model = xgb.Booster()
        self.model.load_model(model_path)

        # Load schema
        self.schema = _load_schema(metadata_path)

        # Precompute for speed
        self._feature_order = self.schema.feature_columns_before_preprocess
        self._classes = self.schema.label_classes

    def validate_features(self, features: Dict[str, Any]) -> None:
        """
        Validate exact keys + numeric values.
        """
        if not isinstance(features, dict):
            raise FeatureValidationError("features must be a dict of {feature_name: value}.")

        expected = set(self._feature_order)
        provided = set(features.keys())

        missing = sorted(list(expected - provided))
        extra = sorted(list(provided - expected))

        if missing or extra:
            msg_parts = []
            if missing:
                msg_parts.append(f"Missing features: {missing}")
            if extra:
                msg_parts.append(f"Unexpected features: {extra}")
            msg_parts.append("Feature set must exactly match metadata['feature_columns_before_preprocess'].")
            raise FeatureValidationError(" | ".join(msg_parts))

        # Numeric-only check
        non_numeric = {k: features[k] for k in self._feature_order if not _is_number(features[k])}
        if non_numeric:
            raise FeatureValidationError(
                "Non-numeric feature values found. Native model expects numeric inputs only. "
                f"Non-numeric: {non_numeric}. "
                "Either map/encode these values or use the full preprocessing pipeline (joblib)."
            )

    def _to_ordered_array(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Convert validated dict into a 2D array with correct ordering.
        """
        row = [float(features[name]) for name in self._feature_order]
        return np.array([row], dtype=float)

    def score_project(
        self,
        features: Dict[str, Any],
        issuance_probability_mode: str = "A_or_B",
    ) -> Dict[str, Any]:
        """
        Score a project and return:
        - ci_class
        - probabilities per class
        - issuance_probability (configurable heuristic)
        - model_version (from metadata if present)

        issuance_probability_mode:
          - "A_or_B": probability(A) + probability(B)
          - "A_only": probability(A)
          - "1_minus_C": 1 - probability(C)
        """
        self.validate_features(features)

        X = self._to_ordered_array(features)
        dmatrix = xgb.DMatrix(X)

        probs = self.model.predict(dmatrix)

        # XGBoost may return shape (n, k). We expect one row.
        if probs.ndim == 2:
            probs_row = probs[0]
        else:
            probs_row = probs

        if len(probs_row) != len(self._classes):
            raise RuntimeError(
                f"Model returned {len(probs_row)} probabilities but metadata has {len(self._classes)} classes."
            )

        probs_dict = {cls: float(p) for cls, p in zip(self._classes, probs_row)}
        predicted_class = self._classes[int(np.argmax(probs_row))]

        if issuance_probability_mode == "A_or_B":
            issuance_prob = probs_dict.get("A", 0.0) + probs_dict.get("B", 0.0)
        elif issuance_probability_mode == "A_only":
            issuance_prob = probs_dict.get("A", 0.0)
        elif issuance_probability_mode == "1_minus_C":
            issuance_prob = 1.0 - probs_dict.get("C", 0.0)
        else:
            raise ValueError("issuance_probability_mode must be one of: A_or_B, A_only, 1_minus_C")

        return {
            "ci_class": predicted_class,
            "probabilities": probs_dict,
            "issuance_probability": float(issuance_prob),
            "schema_version": self.schema.version,
            "schema_notes": self.schema.notes,
            "feature_order": self._feature_order,  # helpful for debugging/audits
        }
