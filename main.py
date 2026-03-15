from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from secrets import token_hex
import uvicorn
import json
import os
from functions import *
from markdown import markdown
from weasyprint import HTML


app = FastAPI(title="Resume Optimizer Backend")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the base directory (where main.py is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("resumes", exist_ok=True)
templates_dir = os.path.join(BASE_DIR, "templates")
static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(templates_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

# Mount static files and configure templates with absolute paths
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)


@app.get("/health")
async def health_check():
    """Health check endpoint for deployment verification"""
    return {
        "status": "healthy",
        "templates_dir": templates_dir,
        "static_dir": static_dir,
        "templates_exist": os.path.exists(templates_dir),
        "static_exist": os.path.exists(static_dir),
        "templates_files": os.listdir(templates_dir) if os.path.exists(templates_dir) else [],
        "static_files": os.listdir(static_dir) if os.path.exists(static_dir) else []
    }

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Landing page inspired by Tsenta marketing site."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/solutions", response_class=HTMLResponse)
async def solutions_page(request: Request):
    """Solutions page where users upload resume & JD."""
    return templates.TemplateResponse("solutions.html", {"request": request})


@app.post("/get-optimised-resume")
async def upload_resume(jd_string, file: UploadFile = File(...), template_id: int = 1, style_id: int = 1):
    """Upload a resume PDF file and JD with selected template and style"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")
        
        file_ext = file.filename.split(".").pop()
        file_name = token_hex(10)
        file_path = f"uploads/{file_name}.{file_ext}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        def extract_pdf_text(path):
            text = ""
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text

        resume_string = extract_pdf_text(file_path)

        prompt = create_prompt(resume_string, jd_string)

        try:
            response_string = get_resume_response(prompt)
        except Exception as e:
            # Clean up then return
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"AI generation error: {e}")
        finally:
            # Clean up the uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)

        # The AI should return a JSON string following the schema in `functions.create_prompt`.
        try:
            parsed = json.loads(response_string)
        except Exception as e:
            # Attempt to find JSON inside text in case the model returned extra text
            try:
                import re
                match = re.search(r"\{[\s\S]*\}\s*$", response_string)
                if match:
                    parsed = json.loads(match.group(0))
                else:
                    raise
            except Exception:
                raise HTTPException(status_code=500, detail=f"Failed to parse AI JSON response: {e}")

        if not isinstance(parsed, dict):
            raise HTTPException(status_code=500, detail="AI response JSON is not an object")

        # Basic validation: ensure some expected keys are present
        expected_keys = ["name", "contact", "summary", "experience", "skills"]
        ok = any(k in parsed for k in expected_keys)
        if not ok:
            raise HTTPException(status_code=500, detail="AI response JSON missing expected resume fields")

        # Load the selected template
        template_filename = f"template{template_id}.html"
        template_path = os.path.join(BASE_DIR, "resume-templates", "resume-templates", "html", template_filename)
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except FileNotFoundError:
            # Fall back to default resume_template if selected not found
            try:
                template = templates.env.get_template('resume_template.html')
                template_content = None
            except Exception:
                raise HTTPException(status_code=500, detail=f"Template {template_filename} not found")
        
        # Load the selected CSS style
        style_filename = f"style{style_id}.css"
        style_path = os.path.join(BASE_DIR, "resume-templates", "resume-templates", "css", style_filename)
        
        css_content = ""
        try:
            with open(style_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
        except FileNotFoundError:
            # Fall back to default style.css if selected not found
            default_style_path = os.path.join(BASE_DIR, 'resumes', 'style.css')
            try:
                with open(default_style_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
            except FileNotFoundError:
                pass

        # Prepare context
        context = {
            "name": parsed.get("name", ""),
            "contact": parsed.get("contact", {}),
            "summary": parsed.get("summary", ""),
            "experience": parsed.get("experience", []),
            "projects": parsed.get("projects", []),
            "skills": parsed.get("skills", []),
            "education": parsed.get("education", []),
            "certifications": parsed.get("certifications", []),
            "achievements": parsed.get("achievements", []),
            "extracurriculars": parsed.get("extracurriculars", []),
            "publications": parsed.get("publications", [])
        }

        # Render template
        if template_content:
            # Use loaded template file
            from jinja2 import Template as Jinja2Template
            jinja_template = Jinja2Template(template_content)
            html_content = jinja_template.render(**context)
            # Replace stylesheet placeholder with inline CSS
            html_content = html_content.replace('href="STYLESHEET_PLACEHOLDER"', '')
            # Add CSS inline before closing head
            html_content = html_content.replace('</head>', f'<style>{css_content}</style></head>')
        else:
            # Use default resume_template.html
            template = templates.env.get_template('resume_template.html')
            html_content = template.render(**context)

        output_pdf_file = "resumes/optimized_resume.pdf"
        try:
            # If using custom template, CSS is already inlined
            if template_content:
                HTML(string=html_content).write_pdf(output_pdf_file)
            else:
                # If using default, use stylesheet
                css_path = os.path.join(BASE_DIR, 'resumes', 'style.css')
                HTML(string=html_content).write_pdf(output_pdf_file, stylesheets=[css_path])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to render PDF: {e}")

        pdf_path = output_pdf_file
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF file not found after generation")

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="optimized_resume.pdf"
        )


    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/get-ats-score")
async def get_score(jd_string, file: UploadFile = File(...)):
    """Upload a resume PDF file and JD"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")
        
        file_ext = file.filename.split(".").pop()
        file_name = token_hex(10)
        file_path = f"uploads/{file_name}.{file_ext}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        def extract_pdf_text(path):
            text = ""
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text
        resume_string=extract_pdf_text(file_path)

        
        try:
            ats_score = ats_scoring(resume_string, jd_string)
            parsed = json.loads(ats_score)
            return parsed
        except Exception as e:
            return f"Failed to generate resume from the AI: {e}", ""
        finally:
            # Clean up the uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
# @app.post("/optimize-resume")
# async def optimize_resume(
#     resume_name: str = Form(..., description="Name of the uploaded resume file"),
#     job_description: str = Form(..., description="Job description text")
# ):
#     """
#     Process an uploaded resume with a job description to create an optimized version.
    
#     Args:
#         file_name: Name of the uploaded resume file in the uploads folder
#         job_description: Text of the job description to optimize for
    
#     Returns:
#         dict: Contains the optimized resume in markdown format
#     """
#     try:
#         # Construct the file path
#         resume_path=f"uploads/{resume_name}"

        
        
#         # Check if file exists
#         if not os.path.exists(resume_path):
#             raise HTTPException(status_code=404, detail=f"Resume file '{resume_name}' not found in uploads folder")
        
#         # Process the resume
#         new_resume = process_resume(resume_name, job_description)
        
#         # if new_resume.startswith("Failed"):
#         #     raise HTTPException(status_code=500, detail=new_resume)
        
#         output_pdf_file = "resumes/optimized_resume.pdf"
#         html_content = markdown(new_resume)
    

#         # Convert HTML to PDF and save (use existing styles filename)
#         HTML(string=html_content).write_pdf(output_pdf_file, stylesheets=['resumes/style.css'])
#         pdf_path = "resumes/optimized_resume.pdf"
#         if not os.path.exists(pdf_path):
#             raise HTTPException(status_code=404, detail="PDF file not found")
        
#         return FileResponse(
#             pdf_path,
#             media_type="application/pdf",
#             filename="optimized_resume.pdf"
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error exporting resume: {str(e)}")


       


# @app.post("/export-resume")
# async def export_resume_endpoint(
#     resume_content: str = Form(..., description="Markdown content of the resume")
# ):
#     """
#     Export the optimized resume to PDF format.
    
#     Args:
#         resume_content: Markdown formatted resume content
    
#     Returns:
#         FileResponse: PDF file download
#     """
#     try:
#         # Export the resume to PDF
#         result = export_resume(resume_content)
        
        
#         # Return the PDF file
#         pdf_path = "resumes/resume_new.pdf"
#         if not os.path.exists(pdf_path):
#             raise HTTPException(status_code=404, detail="PDF file not found")
        
#         return FileResponse(
#             pdf_path,
#             media_type="application/pdf",
#             filename="optimized_resume.pdf"
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error exporting resume: {str(e)}")


# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {
#         "message": "Resume Optimizer API is running",
#         "endpoints": {
#             "POST /upload-resume": "Upload resume PDF file",
#             "POST /optimize-resume": "Process uploaded resume with job description",
#             "POST /export-resume": "Export optimized resume to PDF"
#         }
#     }


# @app.get("/list-resumes")
# async def list_resumes():
#     """List all uploaded resume files"""
#     try:
#         files = [f for f in os.listdir("uploads") if f.endswith('.pdf')]
#         return {
#             "success": True,
#             "files": files,
#             "count": len(files)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


if __name__ == "__main__":
    # For production, use environment variable PORT (set by hosting platforms)
    port = int(os.environ.get("PORT", 8000))
    # Only enable reload in development
    reload = os.environ.get("ENVIRONMENT", "development") == "development"
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=reload)