import pandas as pd
import numpy as np
import re

def get_numerical_column_features(col):
    """
    ========================================
    COLUMN: <column_name>
    ----------------------------------------
    Type            : <dtype>
    Missing %       : <missing_percent>%
    Unique Values   : <num_unique>
    Min             : <min_value>
    Max             : <max_value>
    Mean            : <mean_value>
    Std             : <std_value>
    ========================================
    """
    features = {}
    features['dtype'] = pd.api.types.infer_dtype(col)
    if 'mixed' in features['dtype']:
        type_counts = col.dropna().map(type).value_counts()
        type_percents = type_counts / len(col.dropna()) * 100
        features['composition'] = {t.__name__: f"{c} ({p:.2f}%)" for t, c, p in zip(type_counts.index, type_counts, type_percents)}

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
    """
    ========================================
    COLUMN: <column_name>
    ----------------------------------------
    Type            : <>dtype>
    Missing %       : <missing_count>(<missing_percentage>%)
    Unique Values   : <unique_count>
    Top Values      :
        <entity1>    : <value1> (<percent>%)
        <entity2>    : <value2> (<percent>%)
        <entity3>    : <value3> (<percent>%)
        <entity4>    : <value4> (<percent>%)
        <entity5>    : <value5> (<percent>%)
    Balanced Column  : <Yes/No>
    Cardinality       : <High/Medium/Low>
    ========================================
    """
    features = {}
    features['dtype'] = pd.api.types.infer_dtype(col)
    if 'mixed' in features['dtype']:
        type_counts = col.dropna().map(type).value_counts()
        type_percents = type_counts / len(col.dropna()) * 100
        features['composition'] = {t.__name__: f"{c} ({p:.2f}%)" for t, c, p in zip(type_counts.index, type_counts, type_percents)}

    missing_count = col.isnull().sum()
    missing_percent = col.isnull().mean() * 100
    features['missing_percent'] = list((missing_count, missing_percent))
    features['num_unique'] = col.nunique()
    
    top_values = col.value_counts()
    top_percents = col.value_counts(normalize=True) * 100
    features['top_values'] = list(zip(top_values.index, top_values, top_percents))
    features['balanced'] = not (top_percents.max() > 70)
    features['cardinality'] = 'High' if features['num_unique'] > 10 else 'Medium' if features['num_unique'] > 3 else 'Low'
    features['fd_analysis'] = []

    return features

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

def functional_dependency_analysis(df, col1, col2):
    """
    Analyze functional dependency between two columns.
    Returns a dictionary with the results.
    """
    dependency = {}
    grouped = df.groupby(col1)[col2].nunique()
    total_groups = len(grouped)
    unique_values = grouped.nunique()
    
    dependency['total_groups'] = total_groups
    dependency['unique_values'] = unique_values
    dependency['dependency_ratio'] = unique_values / total_groups if total_groups > 0 else 0
    
    return dependency