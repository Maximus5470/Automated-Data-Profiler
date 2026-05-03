from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from jinja2 import Environment, FileSystemLoader
import json
import os
from pathlib import Path
import tempfile
import shutil
import main as data_profiler

app = FastAPI(title="Data Profiling Dashboard")

# Setup Jinja2 templates
template_dir = Path(__file__).parent / "templates"
template_dir.mkdir(exist_ok=True)
env = Environment(loader=FileSystemLoader(template_dir))

# Uploads directory
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the initial upload page"""
    template = env.get_template('upload.html')
    html_content = template.render()
    return html_content

@app.post("/upload", response_class=HTMLResponse)
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload and generate profile"""
    try:
        # Save uploaded file temporarily
        temp_path = uploads_dir / file.filename
        
        # Save the uploaded file
        contents = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        # Generate profile for the uploaded file
        data_profiler.generate_profile(str(temp_path))
        
        # Load the generated profile
        with open('result.json', 'r') as f:
            profile_data = json.load(f)
        
        # Render the dashboard with the profile data
        template = env.get_template('dashboard.html')
        html_content = template.render(data=profile_data)
        
        return html_content
        
    except Exception as e:
        template = env.get_template('upload.html')
        error_html = template.render(error=str(e))
        return error_html
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()

@app.get("/download-json")
async def download_json():
    """Download result.json file"""
    json_file = Path('result.json')
    if not json_file.exists():
        raise HTTPException(status_code=404, detail="result.json not found")
    
    return FileResponse(
        path=json_file,
        filename="result.json",
        media_type="application/json"
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Load profiling data and render HTML dashboard"""
    # Check if result.json exists, if not generate it
    if not os.path.exists('result.json'):
        data_profiler.generate_profile()
    
    # Load the JSON data
    with open('result.json', 'r') as f:
        profile_data = json.load(f)
    
    # Render the template with data
    template = env.get_template('dashboard.html')
    html_content = template.render(data=profile_data)
    return html_content

@app.post("/refresh")
async def refresh_profile():
    """Regenerate the profile data"""
    data_profiler.generate_profile()
    with open('result.json', 'r') as f:
        profile_data = json.load(f)
    return {"status": "success", "message": "Profile refreshed", "data": profile_data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
