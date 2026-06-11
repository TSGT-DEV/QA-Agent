from typing import Optional
import gradio as gr
from pathlib import Path
from .llm import get_llm, generate_answer

def process_file_and_question(file: Optional[str], question: str) -> str:
    """
    Process uploaded file and question.
    If a question is provided, uses LLM to generate an answer based on file content.
    """
    if file is None:
        return "Please upload a file first."
    
    # Get file extension to determine file type
    file_path = Path(file)
    file_extension = file_path.suffix.lower()
    
    try:
        # Read file content based on type
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
    
    # If no question, return file info and content
    if not question or not question.strip():
        file_info = f"Uploaded file: {file_path.name}"
        return f"{file_info}\n\nFile Content:\n{'-'*50}\n{content}\n{'-'*50}\n\nNo question provided. Please ask a question about the file."
    
    # If there's a question, use LLM to generate answer
    file_info = f"Uploaded file: {file_path.name}"
    llm = get_llm()
    answer = generate_answer(llm, content, question)
    
    return f"{file_info}\n\nFile Content:\n{'-'*50}\n{content}\n{'-'*50}\n\nQuestion: {question}\nAnswer: {answer}"

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
                question_input: gr.Textbox = gr.Textbox(
                    label="Ask a Question (Optional)",
                    placeholder="Enter your question about the uploaded file...",
                    lines=2
                )
                submit_btn: gr.Button = gr.Button("Submit", variant="primary")
            
            with gr.Column():
                output_box: gr.Textbox = gr.Textbox(
                    label="Answer",
                    lines=10,
                    max_lines=20
                )
                 
        # Set up event handling
        # pylint: disable=no-member
        submit_btn.click(
            fn=process_file_and_question,
            inputs=[file_input, question_input],
            outputs=output_box
        )
        # pylint: enable=no-member
   
        # Also allow submitting with Enter key in question box
        # pylint: disable=no-member
        question_input.submit(
            fn=process_file_and_question,
            inputs=[file_input, question_input],
            outputs=output_box
        )
        # pylint: enable=no-member
   
    return demo

def launch_ui() -> None:
    """
    Launches the Gradio UI.
    """
    demo = create_ui()
    demo.launch(inbrowser=False)

if __name__ == "__main__":
    launch_ui()
