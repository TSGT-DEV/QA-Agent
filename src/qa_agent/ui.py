from typing import Any, Optional
import gradio as gr
from pathlib import Path
from .llm import get_llm, generate_answer

def process_file_and_question(
    file: Optional[str],
    question: str,
    output_format: str,
    schema: str
):
    """
    Process uploaded file and question.
    If a question is provided, uses LLM to generate an answer based on file content.
    """
    if file is None:
        return "No file uploaded", "Please upload a file first."
    
    file_path = Path(file)
    file_extension = file_path.suffix.lower()
    
    try:
        if file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_extension == '.pdf':
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                content = ""
                for page in reader.pages:
                    content += page.extract_text() + "\n"
        elif file_extension in ['.docx', '.doc']:
            import docx
            doc = docx.Document(str(file_path))
            content = ""
            for para in doc.paragraphs:
                content += para.text + "\n"
        else:
            content = f"Unsupported file type: {file_extension}\nSupported types: .txt, .pdf, .docx, .doc"
    except ImportError as e:
        if 'PyPDF2' in str(e):
            content = "PyPDF2 is not installed. Please install it to read PDF files."
        elif 'docx' in str(e):
            content = "python-docx is not installed. Please install it to read DOC/DOCX files."
        else:
            content = f"Missing dependency: {str(e)}"
    except Exception as e:
        content = f"Error reading file: {str(e)}"
    
    file_info = f"Uploaded file: {file_path.name}"
    context_display = f"{file_info}\n\n{'-'*50}\n{content}\n{'-'*50}"
    
    if not question or not question.strip():
        return context_display, "No question provided. Please ask a question about the file."
    
    llm = get_llm()
    schema_value = schema.strip() if schema and schema.strip() else None
    answer = generate_answer(llm, content, question, output_format, schema_value)
    
    result = f"Question: {question}\n\nAnswer:\n{answer}"
    return context_display, result

def create_ui():
    """
    Creates and returns the Gradio Blocks interface for the File Q&A System.
    """
    with gr.Blocks(title="File Q&A System") as demo:
        gr.Markdown("# File Question Answering System")
        gr.Markdown("Upload a document (PDF, DOCX, etc.) and ask questions about its content.")
        
        with gr.Row():
            with gr.Column():
                file_input: gr.File = gr.File(
                    label="Upload File",
                    file_types=[".pdf", ".docx", ".doc", ".txt"],
                    type="filepath"
                )
                output_format: gr.Radio = gr.Radio(
                    choices=["text", "json"],
                    value="json",
                    label="Output Format"
                )
                schema_input: gr.Textbox = gr.Textbox(
                    label="Output Schema (Optional)",
                    placeholder="""Enter JSON schema. Schema format: {"field_name": {"type": "string"}} where type can be string, integer, number, or boolean""",
                    lines=2,
                    value="""{"field_name": {"type": "string"}}"""
                )
                question_input: gr.Textbox = gr.Textbox(
                    label="Ask a Question (Optional)",
                    placeholder="Enter your question about the uploaded file...",
                    lines=2,
                    value="List all equipments"
                )
                submit_btn: Any = gr.Button("Submit", variant="primary")
            
            with gr.Column():
                context_box: gr.Textbox = gr.Textbox(
                    label="Context (File Content)",
                    lines=10,
                    max_lines=20,
                    interactive=False
                )
            
            with gr.Column():
                output_box: gr.Textbox = gr.Textbox(
                    label="Question & Answer",
                    lines=10,
                    max_lines=20
                )
                  
        getattr(submit_btn, "click")(
            fn=process_file_and_question,
            inputs=[file_input, question_input, output_format, schema_input],
            outputs=[context_box, output_box]
        )

    return demo

def launch_ui() -> None:
    """
    Launches the Gradio UI.
    """
    demo = create_ui()
    demo.launch(inbrowser=False)

if __name__ == "__main__":
    launch_ui()