# Data Profiling Dashboard

A web-based data profiling application that analyzes CSV, JSON, and MongoDB datasets to generate comprehensive statistical reports and data quality insights.

## Overview

The Data Profiling Dashboard is a FastAPI-based web application designed to help users understand their data through automated profiling and analysis. Upload your data files, and the application will generate detailed statistics about your dataset including column profiling, data types, missing values, duplicates, and functional dependencies.

## Features

- **Multi-format Data Support**: Analyze data from CSV files, JSON files, and MongoDB Atlas databases
- **Comprehensive Profiling**: Automatic analysis of:
  - Table-level statistics (row count, column count, dataset size)
  - Missing values and duplicates detection
  - Column-level profiling (data types, distributions, unique values)
  - Numerical column features (min, max, mean, std deviation)
  - Categorical column features (top values, cardinality, balance)
  - Functional dependencies between columns
- **Web Dashboard**: User-friendly Jinja2-based HTML interface for file upload and result visualization
- **Session Management**: Persistent session storage with cookie-based tracking
- **Data Export**: Download profiling results as JSON files
- **Scalable Processing**: PySpark integration for large dataset handling

## Installation

### Prerequisites

- Python 3.11
- Java Runtime Environment (required for PySpark)

### Setup Instructions

1. **Clone or download the project**
   ```bash
   cd DataProfiling
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   # or
   source venv/bin/activate      # On Linux/macOS
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Application

```bash
python app.py
```

Or using uvicorn directly:

```bash
uvicorn app:app --reload
```

The application will be available at `http://localhost:8000`

### Using the Dashboard

1. **Upload Data**: Navigate to the upload page and select a CSV or JSON file
2. **Automatic Analysis**: The application automatically analyzes the uploaded file
3. **View Results**: See comprehensive statistics and insights about your data
4. **Download Report**: Export the profiling results as a JSON file for further analysis

## API Endpoints

### Dashboard Routes

- `GET /` - Main dashboard page
- `POST /upload` - Upload and analyze a new file
- `GET /results` - View analysis results for current session
- `GET /download/{file_id}` - Download profiling results as JSON

## Technical Details

### Data Type Inference

The `utils.py` module provides intelligent data type detection that handles:
- Null values (empty strings, 'nan', 'none', 'null', 'na', 'n/a', etc.)
- Boolean values ('true', 'false')
- Integers and floats
- Dates and datetimes (ISO 8601 format)
- Strings and text
- Mixed-type columns (with composition tracking)

### Session Management

- Sessions are identified by unique IDs stored in HTTP cookies
- Each session maintains its own upload and results directories
- Session data persists for 30 days
- Session IDs are validated to prevent directory traversal attacks

### Profiling Features

#### Table-Level Statistics
- Number of rows and columns
- Dataset size in megabytes
- Duplicate row detection and percentage
- Overall missing value statistics

#### Column-Level Analysis
- Data type inference
- Missing value percentages
- Unique value counts
- Distribution analysis

#### Numerical Columns
- Min/max values
- Mean and standard deviation
- Type composition for mixed-type columns

#### Categorical Columns
- Top values with counts and percentages
- Cardinality classification (Low/Medium/High)
- Balance analysis (checking if distribution is skewed)
- Type composition for mixed-type columns

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Pandas**: Data manipulation and analysis
- **PySpark**: Distributed data processing
- **Jinja2**: Template engine for HTML rendering
- **NumPy**: Numerical computing
- **MongoDB Spark Connector**: For MongoDB integration
- **Uvicorn**: ASGI server

## Data Source Support

### CSV Files
Automatically loaded with header detection

### JSON Files
Supports both single-object JSON and newline-delimited JSON (NDJSON)

### MongoDB Atlas
Connect to MongoDB using connection URI:
```python
load_mongodb_atlas(uri, database, collection)
```

## Security Features

- HTTP-only cookies for session management
- Session ID validation to prevent directory traversal
- CSRF protection with `samesite="lax"` cookie policy
- Secure cookie transmission over HTTPS

## Example Output

A profiling result includes:

```json
{
  "Number of Columns": 21,
  "Number of Rows": 704,
  "Duplicate Rows": "12 (1.70%)",
  "Missing Values": "45 (0.31%)",
  "Dataset Size": "0.15 MB",
  "column_profiling": {
    "Column Name": {
      "dtype": "object",
      "missing_percent": [0, 0.0],
      "num_unique": 42,
      "top_values": [[value, count, percentage], ...],
      "balanced": true,
      "cardinality": "Medium"
    }
  }
}
```

## Troubleshooting

### PySpark Issues
- Ensure Java is installed and `JAVA_HOME` environment variable is set
- Check that PySpark version matches Java compatibility

### Storage Path Errors
- Check write permissions in the `storage/` directory
- The app will automatically use temp directory as fallback

### MongoDB Connection Issues
- Verify MongoDB Atlas connection string format
- Ensure network access is allowed in MongoDB Atlas security settings