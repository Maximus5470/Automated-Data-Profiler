import pandas as pd
import numpy as np
import re
import json

def get_numerical_column_features(col):
    """Extract features for numerical columns."""
    features = {}
    features['dtype'] = pd.api.types.infer_dtype(col)
    if 'mixed' in features['dtype']:
        counts = col.dropna().map(type).value_counts()
        percents = counts / len(col.dropna()) * 100
        features['composition'] = {t.__name__: f"{c} ({p:.2f}%)" for t, c, p in zip(counts.index, counts, percents)}

    missing_count = col.isnull().sum()
    missing_percent = col.isnull().mean() * 100
    features['missing_percent'] = list((missing_count, missing_percent))
    features['num_unique'] = col.nunique()
    features['min_value'] = col.min()
    features['max_value'] = col.max()
    if pd.api.types.is_numeric_dtype(col):
        features['mean_value'] = round(col.mean(), 2)
        features['std_value'] = round(col.std(), 2)
    
    return features


def get_categorical_column_features(col):
    """Extract features for categorical columns."""
    features = {}
    features['dtype'] = pd.api.types.infer_dtype(col)
    if 'mixed' in features['dtype']:
        counts = col.dropna().map(type).value_counts()
        percents = counts / len(col.dropna()) * 100
        features['composition'] = {t.__name__: f"{c} ({p:.2f}%)" for t, c, p in zip(counts.index, counts, percents)}

    missing_count = col.isnull().sum()
    missing_percent = col.isnull().mean() * 100
    features['missing_percent'] = list((missing_count, missing_percent))
    features['num_unique'] = col.nunique()
    
    top_values = col.value_counts()
    top_percents = col.value_counts(normalize=True) * 100
    features['top_values'] = list(zip(top_values.index, top_values, top_percents))
    features['balanced'] = not (top_percents.max() > 70)
    features['cardinality'] = 'High' if features['num_unique'] > 10 else 'Medium' if features['num_unique'] > 3 else 'Low'

    return features


def make_hashable_cell(value):
    """Convert nested MongoDB values into a stable scalar representation."""
    if isinstance(value, (list, dict, set, tuple, np.ndarray)):
        try:
            return json.dumps(value, default=str, sort_keys=True, ensure_ascii=False)
        except TypeError:
            return json.dumps(str(value), ensure_ascii=False)
    return value

NULL_STRINGS = {'', 'nan', 'none', 'null', 'na', 'n/a', '#n/a', 'missing'}
DATE_RE = re.compile(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:[ T]\d{1,2}:\d{1,2}:\d{1,2})?|^\d{1,2}[-/]\d{1,2}[-/]\d{4}(?:[ T]\d{1,2}:\d{1,2}:\d{1,2})?')

def infer_cell_type(val):
    if not isinstance(val, str):
        return np.nan if (val is None or (isinstance(val, float) and np.isnan(val))) else val

    s = val.strip()

    if s.lower() in NULL_STRINGS:  return np.nan
    if s.lower() == 'true':        return True
    if s.lower() == 'false':       return False

    try: return int(s)
    except: pass

    try: return float(s)
    except: pass

    if DATE_RE.match(s):
        try:
            p = pd.to_datetime(s, errors='raise')
            return p.to_pydatetime()
        except: pass

    return s.strip("'\"")