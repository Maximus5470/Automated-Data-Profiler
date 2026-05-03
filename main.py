import pandas as pd
import utils
import json
import numpy as np

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def generate_profile(csv_path='data/Autism_Data.csv', save_path='result.json'):
    df = pd.read_csv(csv_path, dtype=object)
    df = df.apply(lambda col: col.map(utils.infer_cell_type))

    results = {}

    # Table Profiling
    columns = df.columns
    rows = df.shape[0]
    duplicates = df.duplicated().sum()
    missing_values = df.isnull().sum()
    missing_percent = df.isnull().mean() * 100
    dataset_size = df.memory_usage(deep=True).sum() / (1024 ** 2)

    results["Number of Columns"] = len(columns)
    results["Number of Rows"] = rows
    results["Duplicate Rows"] = f"{duplicates} ({(duplicates/rows)*100:.2f}%)"
    results["Missing Values"] = f"{missing_values.sum()} ({missing_percent.mean():.2f}%)"
    results["Dataset Size"] = f"{dataset_size:.2f} MB"

    numerical_columns = df.select_dtypes(include=['number']).columns
    results['column_profiling'] = {}

    # Functional Dependency 
    dependencies = {k:[] for k in columns}
    for col1 in columns:
        for col2 in columns:
            if col1 != col2:
                dependency = df.groupby(col1)[col2].nunique()
                if (dependency <= 1).all():
                    dependencies[col1].append(col2)

    # Column Profiling
    for column in columns:
        if pd.api.types.is_numeric_dtype(df[column]) or pd.api.types.is_datetime64_any_dtype(df[column]):
            features = utils.get_numerical_column_features(df[column])
            results['column_profiling'][column] = {
                "Type": features['dtype'],
                "Composition": features['composition'] if 'composition' in features else None,
                "Missing %": f"{features['missing_percent'][0]} ({features['missing_percent'][1]:.2f}%)",
                "Unique Values": features['num_unique'],
                "Min": features['min_value'],
                "Max": features['max_value'],
                "Mean": features['mean_value'] if 'mean_value' in features else None,
                "Std": features['std_value'] if 'std_value' in features else None,
                "Functional Dependencies": ', '.join(dependencies[column]) if dependencies[column] else "No strong dependencies"
            }
        else:
            features = utils.get_categorical_column_features(df[column])
            results['column_profiling'][column] = {
                "Type": features['dtype'],
                "Composition": features['composition'] if 'composition' in features else None,
                "Missing %": f"{features['missing_percent'][0]} ({features['missing_percent'][1]:.2f}%)",
                "Unique Values": features['num_unique'],
                "Top Values": {str(entity): f"{value} ({percent:>5.2f}%)" for entity, value, percent in features['top_values']},
                "Balanced Column": 'Yes' if features['balanced'] else 'No',
                "Cardinality": features['cardinality'],
                "Functional Dependencies": ', '.join(dependencies[column]) if dependencies[column] else "No strong dependencies"
            }

    # Cross Column Profiling
    results['cross_column_profiling'] = df[numerical_columns].corr().to_dict()

    # Functional Dependency Analysis
    results['functional_dependency_analysis'] = {column: (', '.join(deps) if deps else "No strong dependencies") for column, deps in dependencies.items()}

    if save_path:
        with open(save_path, 'w') as f:
            json.dump(results, f, indent=4, cls=NpEncoder)
            
    return results

if __name__ == "__main__":
    generate_profile()