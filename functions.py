from openai import OpenAI
from markdown import markdown
from weasyprint import HTML
from dotenv import load_dotenv
import pdfplumber

load_dotenv()

def create_prompt(resume_string,jd_string):
    """Creates a detailed prompt for AI-powered resume optimization based on a job description.

    This function generates a structured prompt that guides the AI to:
    - Tailor the resume to match job requirements
    - Optimize for ATS systems
    - Provide actionable improvement suggestions
    - Format the output in clean Markdown

    Args:
        resume_string (str): The input resume text
        jd_string (str): The target job description text

    Returns:
        str: A formatted prompt string containing instructions for resume optimization"""
    
    return f"""
Your objective is to generate a professional, compelling resume content according to the provided job description, maximizing interview chances by integrating best practices in content quality, keyword optimization, measurable achievements, and proper formatting.

Rewrite the content resume to better match the job description and return in json.
Only improve wording and keyword alignment

IMPORTANT:
You are NOT formatting a resume.
You are ONLY returning structured content.

### OUTPUT RULES (MANDATORY)
- Output **ONLY valid JSON**
- No explanations, no markdown, no extra text

Guidelines to Follow:
1)Keyword and Skill Optimization:
Rule01:If a tool, framework or skill doesn't match the ones mentioned in the Job description but a similar skill is mentioned, replace the tool/skill/framework with that keyword to match the JD. For example, if Tableau is mentioned but the requirement asks for PowerBI, replace it with PowerBI, if . Be ethical, don't replace if it is not logical.

Analyze the job description and identify relevant keywords (hard and soft skills).
Match as much as possible of the job description’s keywords following the rule above to align with applicant tracking systems (ATS).
Prioritize industry-relevant hard skills and soft skills in dedicated sections and throughout bullet points.

Incorporate Measurable Metrics:
Quantify achievements using the XYZ formula if the user has put such quantifications but not formatted it if user has not put anything quantifyable don't do it: Accomplished X, measured by Y, by doing Z.

Include as many  measurable results as possible to clearly demonstrate impact.
Don't use vague statements; use metrics to highlight value and effectiveness.


Content Quality and Language:
Eliminate buzzwords, clichés, and pronouns (e.g., “I,” “me,” “my”).
Use action-oriented, impactful language to emphasize accomplishments over duties.
Replace generic phrases with specific examples that showcase expertise and success.
Focus on selling professional experience, skills, and results, not merely summarizing past roles.

Additional Instructions:
Keyword Optimize and be specific for each section (Professional Summary, Experience, Skills, Education) to reflect relevance to the job.
Ensure consistent formatting, professional fonts
Use concise bullet points, each starting with a strong action verb.

Follow this EXACT schema

{{
  "name": "",

  "contact": {{
    "email": "",
    "phone": "",
    "address": "",
    "linkedin": "",
    "github": "",
    "portfolio": "",
    "kaggle": "",
    "leetcode": "",
    "codeforces": "",
    "codechef": "",
    "google_scholar": ""
  }},

  "summary": "",

  "experience": [
    {{
      "title": "",
      "company": "",
      "dates": "",
      "bullets": []
    }}
  ],

  "projects": [
    {{
      "name": "",
      "Github link":",
      "url":""
      "bullets": []
    }}
  ],

  "skills": [],

  "education": [
    {{
      "degree": "",
      "school": "",
      "year": "",
      "links":""
    }}
  ],

  "certifications": [
    {{
      "name": "",
      "issuer": "",
      "year": "",
      "url":""
    }}
  ],

  "achievements": [],

  "extracurriculars": [
    {{
      "role": "",
      "organization": "",
      "bullets": []
      "url":""
    }}
  ],

  "publications": [
    {{
      "title": "",
      "publisher": "",
      "year": ""
      "url":""
    }}
  ]
}}

My Resume:
{resume_string}
Job Description:
{jd_string}

"""
def get_resume_response(prompt,model="gpt-4o-mini",temperature: float = 0.1):
    """
    Sends a resume optimization prompt to OpenAI's API and returns the optimized resume response.

    This function:
    - Initializes the OpenAI client
    - Makes an API call with the provided prompt
    - Returns the generated response

    Args:
        prompt (str): The formatted prompt containing resume and job description
        api_key (str): OpenAI API key for authentication
        model (str, optional): The OpenAI model to use. Defaults to "gpt-4-turbo-preview"
        temperature (float, optional): Controls randomness in the response. Defaults to 0.7

    Returns:
        str: The AI-generated optimized resume and suggestions

    Raises:
        OpenAIError: If there's an issue with the API call
    """
    #Setting up openAI client
    client=OpenAI()

    #Make call
    response=client.chat.completions.create(model=model,
                                            response_format={"type": "json_object"},
                                            messages=[
                                                {'role':'system',"content":'Expert resume writer and reviewer'},
                                                {'role':'user','content':prompt}
                                            ],temperature=temperature)
    return response.choices[0].message.content

def ats_scoring(resume_string, jd_string):
    """Gives ats score for the resume highlignting strengths and weaknesses"""
    base_prompt=f"""You are a professional Applicant Tracking System (ATS) resume scanner similar to Jobscan.
    Your task is to analyze a resume against a job description and generate a Jobscan-style Match Report.
    Output ONLY valid JSON. Do NOT wrap the JSON in quotes
    INPUTS 
    Resume:
    {resume_string}
    Job Description:
    {jd_string}
  
    ANALYSIS INSTRUCTIONS
    Evaluate the resume using ATS logic based on:
    - Searchability: 1)Contact information : is email present ,is phone number present, is name present
                     2)Professional summary: is it present, presents my abilities clearly and precisely, is it relevant to the job description
                     3)Section Headings: are Work Experience, Education, Skills, Projects present
                     4) Does Job title Match
                     5)Are the dates in chronological order
                     6) Are there any spelling mistakes in the resume
                     7) Does the resume have relevant links to all projects and achievements
    - Hard skills and Soft skills  match
    - cliches : Does the resume have generic cliche words with no measurable impact.
    - Experience relevance: does the candidate have the experience required in the JD
    - Formatting: 1) Is the resume free from any pictures, watermarks
                  2) Is the resume single column
                  3) Does the resume have too much color and design (too much means more than two)
                  4) Does the resume have unessacery sections like extracurriculars, hobbies, interests
    Be strict, realistic, and recruiter-focused.
    Do NOT assume or hallucinate skills or experience not explicitly stated.

    ### SCORING
    - Compute a Match Rate between 0 and 100
    - Weighting:
    - Hard skills keywords: 40%
    - Experience & cliches: 10%
    - Searchability & formatting: 50%

    ### OUTPUT RULES (MANDATORY)
    - Output **ONLY valid JSON**
    - No explanations, no markdown, no extra text
    - JSON must strictly follow the schema below

    ### REQUIRED JOBSCAN-STYLE JSON FORMAT
    """
    json_schema='''{
    "match_rate": <integer 0-100>,
    "match_level": "<Poor | Fair | Good | Strong | Excellent>",

    "hard_skills": {
        "matched": ["<skill1>", "<skill2>"],
        "missing": ["<skill1>", "<skill2>"]
    },
    "soft_skills": {
        "matched": ["<skill1>", "<skill2>"],
        "missing": ["<skill1>", "<skill2>"]
    },
    "keywords": {
        "matched": ["<keyword1>", "<keyword2>"],
        "missing": ["<keyword1>", "<keyword2>"]
    },
    "tools_and_technologies": {
        "matched": ["<tool1>", "<tool2>"],
        "missing": ["<tool1>", "<tool2>"]
    },

    "experience": {
        "job_requirement": "<years or description from JD>",
        "resume_experience": "<summary of experience from resume>",
        "match_status": "<Low | Partial | Strong>",
        "relevance_score": <integer 0-100>,
        "notes": "<short explanation of how well the experience matches the JD>"
    },

    "job_title_match": {
        "job_title_in_jd": "<title from JD>",
        "resume_titles": ["<title1 from resume>", "<title2 from resume>"],
        "match_status": "<Low | Partial | Strong>"
    },

    "searchability": {
        "score": <integer 0-100>,
        "contact_information": {
        "has_name": <true | false>,
        "has_email": <true | false>,
        "has_phone": <true | false>
        },
        "professional_summary": {
        "is_present": <true | false>,
        "is_clear_and_concise": <true | false>,
        "is_relevant_to_jd": <true | false>
        },
        "section_headings": {
        "has_work_experience": <true | false>,
        "has_education": <true | false>,
        "has_skills": <true | false>,
        "has_projects": <true | false>,
        "missing_sections": ["<missing_section1>", "<missing_section2>"]
        },
        "chronology": {
        "is_chronological": <true | false>,
        "issues": ["<issue about date ordering, if any>"]
        },
        "spelling_grammar": {
        "has_spelling_or_grammar_errors": <true | false>,
        "examples": ["<example error 1>", "<example error 2>"]
        },
        "links": {
        "has_relevant_links": <true | false>,
        "missing_recommended_links": ["<missing_link_description1>", "<missing_link_description2>"]
        },
        "issues": [
        "<high-level searchability issue 1>",
        "<high-level searchability issue 2>"
        ]
    },

    "cliches": {
        "has_cliches": <true | false>,
        "examples": ["<cliche phrase 1>", "<cliche phrase 2>"]
    },

    "formatting": {
        "is_photo_free": <true | false>,
        "is_single_column": <true | false>,
        "has_minimal_color_and_design": <true | false>,  // false if more than two strong colors/design elements
        "unnecessary_sections_present": <true | false>,
        "unnecessary_sections": ["<section name 1>", "<section name 2>"]
    },

    "recruiter_tips": [
        "<actionable improvement 1 based on above analysis>",
        "<actionable improvement 2>",
        "<actionable improvement 3>"
    ]} '''
    prompt = base_prompt + "\n" + json_schema
    model="gpt-4o-mini"
    temperature=0.1
    client=OpenAI()

    #Make call
    response=client.chat.completions.create(model=model,
                                            messages=[
                                                {'role':'system',"content":'Applicant Tracking System (ATS) resume scanner similar to Jobscan'},
                                                {'role':'user','content':prompt}
                                            ],temperature=temperature)
    return response.choices[0].message.content

def process_resume(resume_name,jd_string):
    """
    Process a resume file against a job description to create an optimized version.

    Args:
        resume (file): A file object containing the resume in markdown format
        jd_string (str): The job description text to optimize the resume against

    Returns:
        tuple: A tuple containing three elements:
            - str: The optimized resume in markdown format (for display)
            - str: The same optimized resume (for editing)
            
    """
     
    def extract_pdf_text(path):
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    resume_string=extract_pdf_text(f"uploads/{resume_name}")

    # create prompt
    prompt = create_prompt(resume_string, jd_string)

    # Generate response
    try:
        response_string = get_resume_response(prompt)
    except Exception as e:
        return f"Failed to generate resume from the AI: {e}", ""

    # Return two outputs to match Gradio: Markdown display and editable text
    new_resume = response_string
    return new_resume
    # try:
    #     output_pdf_file = "resumes/optimized_resume.pdf"

    #     # convert markdown to HTML
    #     html_content = markdown(new_resume)

    #     # Convert HTML to PDF and save (use existing styles filename)
    #     HTML(string=html_content).write_pdf(output_pdf_file, stylesheets=['resumes/style.css'])
    #     return f"Successfully exported resume to {output_pdf_file} 🎉"
    # except Exception as e:
    #     return f"Failed to export resume: {str(e)} 💔"