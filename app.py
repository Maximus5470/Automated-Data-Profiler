from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader
import json
from pathlib import Path
import main as data_profiler
import uuid
import re

app = FastAPI(title="Data Profiling Dashboard")

template_dir = Path(__file__).parent / "templates"
template_dir.mkdir(exist_ok=True)
env = Environment(loader=FileSystemLoader(template_dir))

uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(exist_ok=True)

results_dir = Path(__file__).parent / "results"
results_dir.mkdir(exist_ok=True)
manifest_path = results_dir / "manifest.json"


def load_analysis_manifest() -> dict:
    if not manifest_path.exists():
        return {}

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return manifest if isinstance(manifest, dict) else {}
    except Exception:
        return {}


def save_analysis_manifest(manifest: dict) -> None:
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

def validate_file_id(file_id: str) -> str:
    """Validate that file_id contains only safe characters and no path traversal."""
    if not re.match(r'^[A-Za-z0-9_\-]+$', file_id):
        raise ValueError(f"Invalid file_id: {file_id}")
    return file_id

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    safe_name = re.sub(r'[^A-Za-z0-9._-]', '_', filename)
    safe_name = safe_name.strip('.')
    return safe_name or 'file'

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the initial upload page"""
    template = env.get_template('upload.html')
    html_content = template.render()
    return html_content

@app.post("/upload")
async def upload_file(files: List[UploadFile] = File(...)):
    """Handle multiple file uploads and generate profile."""
    results = []
    errors = []
    first_file_id = None
    manifest = load_analysis_manifest()

    for file in files:
        unique_suffix = str(uuid.uuid4())[:8]
        safe_basename = sanitize_filename(Path(file.filename).stem)
        file_id = f"{safe_basename}_{unique_suffix}"
        validate_file_id(file_id)
        
        if not first_file_id:
            first_file_id = file_id
        
        temp_path = uploads_dir / f"temp_{file_id}.csv"

        try:
            if not str(temp_path.resolve()).startswith(str(uploads_dir.resolve())):
                raise ValueError("Invalid temp path")
            
            contents = await file.read()
            with open(temp_path, 'wb') as f:
                f.write(contents)

            result_path = results_dir / f"{file_id}.json"
            if not str(result_path.resolve()).startswith(str(results_dir.resolve())):
                raise ValueError("Invalid result path")
            
            data_profiler.generate_profile(str(temp_path), str(result_path))

            manifest[file_id] = file.filename
            save_analysis_manifest(manifest)

            results.append({"file": file.filename, "file_id": file_id, "result": str(result_path)})

        except Exception as e:
            errors.append({"file": file.filename, "error": str(e)})

        finally:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass

    status_code = 200 if not errors else 207
    return JSONResponse(status_code=status_code, content={"status": "partial" if errors else "success", "processed": results, "errors": errors, "file_id": first_file_id})

@app.get("/download-json/{file_id}")
async def download_json(file_id: str):
    """Download the JSON report for a specific analysis."""
    try:
        validated_id = validate_file_id(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file_id")

    json_file = results_dir / f"{validated_id}.json"
    if not str(json_file.resolve()).startswith(str(results_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file_id")

    if not json_file.exists():
        raise HTTPException(status_code=404, detail="Analysis JSON not found")

    return FileResponse(
        path=json_file,
        filename=f"{validated_id}.json",
        media_type="application/json"
    )

@app.get("/analysis/{file_id}")
async def view_analysis(file_id: str):
    """Load specific profiling data and render HTML dashboard"""
    try:
        validated_id = validate_file_id(file_id)
    except ValueError:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    result_path = results_dir / f"{validated_id}.json"
    if not str(result_path.resolve()).startswith(str(results_dir.resolve())):
        return RedirectResponse(url="/dashboard", status_code=302)
    
    if not result_path.exists():
        return RedirectResponse(url="/dashboard", status_code=302)
    
    with open(result_path, 'r') as f:
        profile_data = json.load(f)

    manifest = load_analysis_manifest()
    analyses = []
    for result_file in sorted(results_dir.glob("*.json")):
        if result_file.name == manifest_path.name:
            continue

        file_id = result_file.stem
        analyses.append({
            "id": file_id,
            "label": manifest.get(file_id, file_id),
        })
    
    template = env.get_template('dashboard.html')
    html_content = template.render(data=profile_data, current_file=validated_id, analyses=analyses)
    return HTMLResponse(content=html_content)

@app.delete("/analysis/{file_id}")
async def delete_analysis(file_id: str):
    """Delete an analysis report and its JSON file."""
    try:
        validated_id = validate_file_id(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file_id")
    
    result_path = results_dir / f"{validated_id}.json"
    if not str(result_path.resolve()).startswith(str(results_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file_id")
    
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    try:
        result_path.unlink()
        manifest = load_analysis_manifest()
        if validated_id in manifest:
            manifest.pop(validated_id, None)
            save_analysis_manifest(manifest)
        return {"status": "success", "message": f"Analysis {validated_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not delete analysis: {str(e)}")

@app.get("/dashboard", response_class=RedirectResponse)
async def dashboard():
    """Redirect to the first available analysis or upload page"""
    analyses = [f.stem for f in results_dir.glob("*.json") if f.name != manifest_path.name]
    if analyses:
        return RedirectResponse(url=f"/analysis/{analyses[0]}")
    return RedirectResponse(url="/")

@app.post("/refresh/{file_id}")
async def refresh_profile(file_id: str):
    """Regenerate the profile data (requires original file if implementing properly)"""
    return {"status": "error", "message": "Not implemented for dynamic routing"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
