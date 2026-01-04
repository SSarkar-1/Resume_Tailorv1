import gradio as gr

def export_resume(resume_md):
    # Here, you would implement the logic to convert the resume markdown to a PDF file and save it
    # For demonstration, we assume it's saved as 'tailored_resume.pdf'
    resume_path = "tailored_resume.pdf"
    
    # Return the file path for Gradio to handle download
    return resume_path

with gr.Blocks() as app:
    # Create header and app description
    gr.Markdown("# Resume Optimizer 📄")
    gr.Markdown("Upload your resume, paste the job description, and get actionable insights!")

    # Gather inputs
    with gr.Row():
        resume_input = gr.File(label="Upload Your Resume (.pdf)")
        jd_input = gr.Textbox(label="Paste the Job Description Here", lines=9, interactive=True, placeholder="Paste job description...")

    # Display output for the tailored resume
    output_resume_file = gr.File(label="Download Tailored Resume")

    # Button to trigger the resume export
    export_button = gr.Button("Export Resume as PDF 🚀")

    # Event binding: When the button is clicked, process the resume and return the file
    export_button.click(
        export_resume,
        inputs=[resume_input, jd_input],
        outputs=[output_resume_file]
    )

# Launch the app
app.launch()
