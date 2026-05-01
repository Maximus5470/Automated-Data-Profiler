import pandas as pd

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
    features['dtype'] = col.dtype
    missing_count = col.isnull().sum()
    missing_percent = col.isnull().mean() * 100
    features['missing_percent'] = list((missing_count, missing_percent))
    features['num_unique'] = col.nunique()
    features['min_value'] = col.min()
    features['max_value'] = col.max()
    features['mean_value'] = col.mean()
    features['std_value'] = col.std()
    
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
    features['dtype'] = col.dtype
    missing_count = col.isnull().sum()
    missing_percent = col.isnull().mean() * 100
    features['missing_percent'] = list((missing_count, missing_percent))
    features['num_unique'] = col.nunique()
    
    top_values = col.value_counts().nlargest(5)
    top_percents = col.value_counts(normalize=True) * 100
    features['top_values'] = list(zip(top_values.index, top_values, top_percents))
    features['balanced'] = not (top_percents.max() > 70)
    features['cardinality'] = 'High' if features['num_unique'] > 10 else 'Medium' if features['num_unique'] > 3 else 'Low'
    return features