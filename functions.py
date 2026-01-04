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
Your objective is to generate a professional, 1-page, compelling resume tailored to the provided job description, maximizing interview chances by integrating best practices in content quality, keyword optimization, measurable achievements, and proper formatting.



If a tool, framework or skill doesn't match the ones mentioned in the Job description but a similar skill is mentioned, replace the tool/skill/framework with that keyword to match the JD. For example, if Tableau is mentioned but the requirement asks for PowerBI, replace it with PowerBI. Be ethical, don't replace if it is not logical.



Guidelines to Follow:



Keyword and Skill Optimization:

Analyze the job description and identify relevant keywords (hard and soft skills).

Match at least 80% of the job description’s keywords to align with applicant tracking systems (ATS).

Prioritize industry-relevant hard skills and soft skills in dedicated sections and throughout bullet points.

Incorporate Measurable Metrics:



Quantify achievements using the XYZ formula: Accomplished X, measured by Y, by doing Z.

Include at least five measurable results that clearly demonstrate impact.

Avoid vague statements; use metrics to highlight value and effectiveness.



Resume Length and Structure:

Keep the resume between 400-500 words for optimal readability and engagement.

Maintain a clean, organized structure with clear headings and bullet points.

Exceptions for roles requiring longer resumes (e.g., academia, federal jobs, C-suite) should be appropriately handled.

Content Quality and Language:



Eliminate buzzwords, clichés, and pronouns (e.g., “I,” “me,” “my”).

Use action-oriented, impactful language to emphasize accomplishments over duties.

Replace generic phrases with specific examples that showcase expertise and success.

Focus on selling professional experience, skills, and results, not merely summarizing past roles.

Additional Instructions:



Customize each section (Professional Summary, Experience, Skills, Education) to reflect relevance to the job.

Ensure consistent formatting, professional fonts, and appropriate use of whitespace.

Use concise bullet points, each starting with a strong action verb.

My Resume:
{resume_string}
Job Description:
{jd_string}


Generate the resume in markdown format to be further written to a PDF file. Return only the resume content and nothing else.Return raw Markdown only.
Do NOT wrap the output in ``` or ```markdown.

"""
def get_resume_response(prompt,model="gpt-4o-mini",temperature: float = 0.7):
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
                                            messages=[
                                                {'role':'System',"content":'Expert resume writer and reviewer'},
                                                {'role':'user','content':prompt}
                                            ],temperature=temperature)
    return response.choices[0].message.content

def process_resume(resume,jd_string):
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
    resume_string=extract_pdf_text("resumes/resume.pdf")

    # create prompt
    prompt = create_prompt(resume_string, jd_string)

    # Generate response
    try:
        response_string = get_resume_response(prompt)
    except Exception as e:
        return f"Failed to generate resume from the AI: {e}", ""

    # Return two outputs to match Gradio: Markdown display and editable text
    new_resume = response_string
    return new_resume, new_resume
def export_resume(new_resume):
    """
    Convert a markdown resume to PDF format and save it.

    Args:
        new_resume (str): The resume content in markdown format

    Returns:
        str: A message indicating success or failure of the PDF export
    """
    try:
        output_pdf_file = "resumes/resume_new.pdf"

        # convert markdown to HTML
        html_content = markdown(new_resume)

        # Convert HTML to PDF and save (use existing styles filename)
        HTML(string=html_content).write_pdf(output_pdf_file, stylesheets=['resumes/style.css'])
        return f"Successfully exported resume to {output_pdf_file} 🎉"
    except Exception as e:
        return f"Failed to export resume: {str(e)} 💔"