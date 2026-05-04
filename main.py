import pandas as pd
import utils
import json
import numpy as np
from pathlib import Path
from datetime import date, datetime

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)): return obj.item()
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, pd.Timestamp): return obj.isoformat()
        if isinstance(obj, (datetime, date)): return obj.isoformat()
        return super().default(obj)


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.astype(object, copy=False)
    df = df.apply(lambda col: col.map(utils.infer_cell_type))
    return df.apply(lambda col: col.map(utils.make_hashable_cell))


def load_csv(csv_path: str, dtype=object) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype=dtype)
    return normalize_dataframe(df)


def load_json(json_path: str, orient: str = "records") -> pd.DataFrame:
    df = pd.read_json(json_path, orient=orient)
    df = df.astype(object, copy=False)
    return normalize_dataframe(df)

def load_mongodb_atlas(uri: str, database: str, collection: str, query: dict | None = None, projection: dict | None = None) -> pd.DataFrame:
    try:
        from pymongo import MongoClient
    except ImportError as exc:
        raise ImportError("pymongo is required to load MongoDB Atlas data; install it with `pip install pymongo`.") from exc

    client = MongoClient(uri)
    try:
        cursor = client[database][collection].find(query or {}, projection)
        df = pd.DataFrame(list(cursor))
    finally:
        client.close()

    if '_id' in df.columns:
        df['_id'] = df['_id'].astype(str)

    df = df.astype(object, copy=False)
    return normalize_dataframe(df)


def infer_source_type(source_path: str) -> str:
    extension = Path(source_path).suffix.lower()
    if extension == '.csv':
        return 'csv'
    if extension in {'.json', '.ndjson'}:
        return 'json'
    raise ValueError(f"Unsupported file type: {extension}")


def load_data(source_path: str, source_type: str | None = None, **kwargs) -> pd.DataFrame:
    source_type = source_type or infer_source_type(source_path)
    if source_type == 'csv':
        return load_csv(source_path, **kwargs)
    if source_type == 'json':
        return load_json(source_path, **kwargs)
    raise ValueError(f"Unsupported source type: {source_type}")


def generate_profile(source_path='data/Autism_Data.csv', save_path='results/result.json', source_type: str | None = None, df: pd.DataFrame | None = None, **kwargs):
    if df is None:
        df = load_data(source_path, source_type=source_type, **kwargs)
    else:
        df = normalize_dataframe(df)

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

    if save_path:
        save_path = Path(save_path)
        # Ensure parent directory exists when a nested path is provided
        if save_path.parent and not save_path.parent.exists():
            try:
                save_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                # If we cannot create the directory, we'll attempt to write and raise a clear error on failure
                pass
        try:
            with open(save_path, 'w') as f:
                json.dump(results, f, indent=4, cls=NpEncoder)
        except OSError as exc:
            raise OSError(f"Unable to write results to {save_path}: {exc}") from exc
            
    return results

if __name__ == "__main__":
    generate_profile()