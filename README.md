# Resume Optimizer

AI-powered resume optimization: ATS score analysis and job-description–tailored resume generation.

## Run on localhost

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your OpenAI API key**  
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Start the app**
   ```bash
   python main.py
   ```

4. **Open in browser**
   - Landing page: http://localhost:8000
   - Solutions (upload resume + JD): http://localhost:8000/solutions
   - Health check: http://localhost:8000/health

### Optional: run with uvicorn (auto-reload on code changes)
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Features

- **Landing page** – Marketing-style homepage
- **Solutions page** – Upload PDF resume and paste job description
- **Get ATS Score** – Strengths, weaknesses, keywords, recruiter tips
- **Optimize Resume** – Download a tailored PDF resume

## Requirements

- Python 3.10+
- OpenAI API key
- PDF resume for upload
