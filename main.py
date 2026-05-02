import pandas as pd
import utils

# Load the dataset
df = pd.read_csv('data/test_datatypes.csv', dtype=object)
# Infer cell types
df = df.apply(lambda col: col.map(utils.infer_cell_type))

# Table Profiling
columns = df.columns
rows = df.shape[0]
duplicates = df.duplicated().sum()
missing_values = df.isnull().sum()
missing_percent = df.isnull().mean() * 100
Dataset_size = df.memory_usage(deep=True).sum() / (1024 ** 2)

# Table Profiling
print(f"========================================")
print(f"TABLE PROFILING")
print(f"----------------------------------------")
print(f"Number of Columns : {len(columns)}")
print(f"Number of Rows    : {rows}")
print(f"Duplicate Rows    : {duplicates} ({(duplicates/rows)*100:.2f}%)")
print(f"Missing Values    : {missing_values.sum()} ({missing_percent.mean():.2f}%)")
print(f"Dataset Size      : {Dataset_size:.2f} MB\n")

numerical_columns = df.select_dtypes(include=['number']).columns

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

# Cross Column Profiling
print(f"========================================")
print(f"CROSS COLUMN PROFILING")
print(f"----------------------------------------")
print(df[numerical_columns].corr())