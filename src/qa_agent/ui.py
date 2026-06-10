from typing import Optional
import gradio as gr

def process_file_and_question(file: Optional[str], question: str) -> str:
    """
    Placeholder function for processing uploaded file and question.
    This will be replaced with actual backend logic later.
    """
    if file is None:
        return "Please upload a file first."
    
    # For now, just return file info and question if provided
    file_info = f"Uploaded file: {file}"
    if question and question.strip():
        return f"{file_info}\nQuestion: {question}\nAnswer: [Placeholder - Backend logic to be implemented]"
    else:
        return f"{file_info}\nNo question provided. Please ask a question about the file."

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
  
    return demo

def launch_ui():
    """
    Launches the Gradio UI.
    """
    demo = create_ui()
    demo.launch(inbrowser=False)

if __name__ == "__main__":
    launch_ui()