"""Shared, serializable preprocessing for training and ChurnGuard inference."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FIX_COLS = ("tenure", "account_user_count", "rev_per_month", "rev_growth_yoy", "coupon_used_for_payment", "day_since_cc_connect", "cashback")
DISCRETE_CANDIDATES = ("account_user_count", "complain_ly")
CATEGORY_MAPS = {
    "gender": {"m": "male", "f": "female"},
    "login_device": {"&&&&": "others"},
    "account_segment": {"regular +": "regular plus", "super +": "super plus"},
}

class NormalizeChurnFeatures(BaseEstimator, TransformerMixin):
    """Normalize numeric and categorical features while preserving column names."""

    def fit(self, X, y=None):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame")
        self.feature_names_in_ = list(X.columns)
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame")

        missing = set(self.feature_names_in_) - set(X.columns)
        if missing:
            raise ValueError(f"Missing required features: {sorted(missing)}")

        out = X.loc[:, self.feature_names_in_].copy()

        # Convert numeric text
        for col in NUMERIC_FIX_COLS:
            if col in out:
                out[col] = pd.to_numeric(out[col], errors="coerce")

        # Normalize categorical values
        for col in out.columns:
            if col not in NUMERIC_FIX_COLS and (
                pd.api.types.is_object_dtype(out[col])
                or pd.api.types.is_string_dtype(out[col])
            ):
                out[col] = (
                    out[col].astype("string")
                    .str.strip()
                    .str.lower()
                    .astype(object)
                )

        # Standardize categorical labels
        for col, mapping in CATEGORY_MAPS.items():
            if col in out:
                out[col] = out[col].replace(mapping)

        # Ensure compatibility with sklearn SimpleImputer
        out = out.astype(object).replace({pd.NA: np.nan})

        return out


def build_preprocessor(X):
    """Create unfitted preprocessing; call on the raw feature DataFrame."""
    num_cols = list(dict.fromkeys(list(X.select_dtypes(include="number").columns) + [c for c in NUMERIC_FIX_COLS if c in X.columns]))
    cat_cols = [c for c in X.columns if c not in num_cols]
    discrete_cols = [c for c in DISCRETE_CANDIDATES if c in num_cols]
    continuous_cols = [c for c in num_cols if c not in discrete_cols]
    columns = ColumnTransformer([
        ("continuous", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), continuous_cols),
        ("discrete", SimpleImputer(strategy="most_frequent"), discrete_cols),
        ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), cat_cols),
    ])
    return Pipeline([("normalize", NormalizeChurnFeatures()), ("columns", columns)])
