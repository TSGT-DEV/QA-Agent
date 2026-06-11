import logging
from typing import Optional
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable

logger = logging.getLogger(__name__)

def get_llm(model_name: str = "llama3.2:1b") -> Optional[OllamaLLM]:
    """
    Initialize and return an Ollama LLM instance.
    Assumes Ollama is running locally and the model is available.
    """
    try:
        llm = OllamaLLM(model=model_name)
        # Test the connection by invoking a simple prompt
        llm.invoke("test")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize Ollama model {model_name}: {e}")
        return None

def generate_answer(llm: Optional[OllamaLLM], context: str, question: str) -> str:
    """
    Generate an answer to the question based on the provided context using the LLM.
    """
    if llm is None:
        return "Error: LLM is not available. Please ensure Ollama is running and the model 'llama3.2:1b' is available."
    
    # Create a prompt template
    template = """Based on the following context, answer the question. If the answer cannot be found in the context, say so.

Context:
{context}

Question:
{question}

Answer:"""
    
    prompt = PromptTemplate.from_template(template)
    
    # Create a chain: format the prompt with context and question, then pass to LLM
    chain: RunnableSerializable[dict[str, str], str] = ( # type: ignore
        {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    try:
        answer = chain.invoke({"context": context, "question": question})
        return answer.strip()
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return f"Error generating answer: {str(e)}"