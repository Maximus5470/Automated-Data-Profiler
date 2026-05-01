import pandas as pd
import utils
import pprint

# Load the dataset
df = pd.read_csv('data/Autism_Data.arff')

# List of columns
columns = df.columns

# Column Profiling
for column in columns:
    if pd.api.types.is_numeric_dtype(df[column]):
        features = utils.get_numerical_column_features(df[column])
        print(f"========================================")
        print(f"COLUMN: {column}")
        print(f"----------------------------------------")
        print(f"Type            : {features['dtype']}")
        print(f"Missing %       : {features['missing_percent'][0]} ({features['missing_percent'][1]:.2f}%)")
        print(f"Unique Values   : {features['num_unique']}")
        print(f"Min             : {features['min_value']}")
        print(f"Max             : {features['max_value']}")
        print(f"Mean            : {features['mean_value']:.4f}")
        print(f"Std             : {features['std_value']:.4f}\n")
    else:
        features = utils.get_categorical_column_features(df[column])
        print(f"========================================")
        print(f"COLUMN: {column}")
        print(f"----------------------------------------")
        print(f"Type            : {features['dtype']}")
        print(f"Missing %       : {features['missing_percent'][0]} ({features['missing_percent'][1]:.2f}%)")
        print(f"Unique Values   : {features['num_unique']}")
        print(f"Top Values      :")
        for entity, value, percent in features['top_values']:
            print(f"    {entity:<12}: {value} ({percent:>5.2f}%)")
        print(f"Balanced Column  : {'Yes' if features['balanced'] else 'No'}")
        print(f"Cardinality       : {features['cardinality']}")
        print()

