import logging
import json
import traceback
from typing import Any, Dict, List, Optional, Type, cast
from pydantic import BaseModel, create_model
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

logger = logging.getLogger(__name__)

JSON_SCHEMA_TYPES: Dict[str, Type[Any]] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}


def _is_object_schema(schema_value: Dict[str, Any]) -> bool:
    schema_type = str(schema_value.get("type", ""))
    if schema_type == "object" or isinstance(schema_value.get("properties"), dict):
        return True
    if "type" in schema_value:
        return False
    return all(isinstance(value, dict) for value in schema_value.values())


def _create_response_model_from_schema_dict(
    schema: Dict[str, Any],
    model_name: str,
) -> Type[BaseModel]:
    fields: Dict[str, Any] = {}
    for key, value in schema.items():
        if isinstance(value, dict):
            schema_value: Dict[str, Any] = cast(Dict[str, Any], value)
            fields[key] = (_get_field_type(schema_value, model_name), ...)
        else:
            fields[key] = (str, ...)
    return create_model(model_name, **fields)


def _get_field_type(schema_value: Dict[str, Any], model_name: str = "DynamicResponse") -> Any:
    schema_type = str(schema_value.get("type", "string"))
    field_type: Any = JSON_SCHEMA_TYPES.get(schema_type, str)

    if schema_type == "array":
        field_type = List[str]
        items = schema_value.get("items")
        if isinstance(items, dict):
            item_schema: Dict[str, Any] = cast(Dict[str, Any], items)
            if _is_object_schema(item_schema):
                item_model = _create_response_model_from_schema_dict(
                    item_schema,
                    f"{model_name}Item",
                )
                field_type = List[item_model]  # type: ignore[valid-type]
            else:
                item_type = _get_field_type(item_schema, f"{model_name}Item")
                field_type = List[item_type]  # type: ignore[valid-type]
    elif schema_type == "object":
        properties = schema_value.get("properties")
        if isinstance(properties, dict):
            field_type = _create_response_model_from_schema_dict(
                cast(Dict[str, Any], properties),
                f"{model_name}Object",
            )
        else:
            field_type = Dict[str, Any]
    elif _is_object_schema(schema_value):
        field_type = _create_response_model_from_schema_dict(schema_value, f"{model_name}Object")

    return field_type


def create_response_model_from_schema(schema_str: Optional[str]) -> Type[BaseModel]:
    """Create a Pydantic model from a JSON schema string."""
    if not schema_str or not schema_str.strip():
        return AnswerResponse

    try:
        raw = json.loads(schema_str.strip())
        if not isinstance(raw, dict):
            return AnswerResponse
        schema: Dict[str, Any] = cast(Dict[str, Any], raw)
        return _create_response_model_from_schema_dict(schema, "DynamicResponse")
    except (json.JSONDecodeError, Exception):
        pass
    return AnswerResponse


class AnswerResponse(BaseModel):
    """Pydantic model for a simple LLM answer response."""
    answer: str


def get_llm(model_name: str = "llama3.2:1b") -> Optional[ChatOllama]:
    """
    Initialize and return an Ollama LLM instance.
    Assumes Ollama is running locally and the model is available.
    """
    try:
        llm = ChatOllama(model=model_name)
        llm.invoke("test")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize Ollama model {model_name}: {e}")
        return None


def generate_answer(
    llm: Optional[ChatOllama],
    context: str,
    question: str,
    output_format: str = "plain",
    schema: Optional[str] = None,
) -> str:
    """
    Generate an answer to the question based on the provided context using the LLM.

    Args:
        llm: The language model to use
        context: The context document content
        question: The question to answer
        output_format: Output format - "plain", "json", or "xml"
        schema: Optional schema definition for structured output (JSON schema for JSON format)
    """
    if llm is None:
        error_msg = "Error: LLM is not available. Please ensure Ollama is running and the model 'llama3.2:1b' is available."
        logger.error(error_msg)
        return error_msg

    template = """Based on the following context, answer the question. If the answer cannot be found in the context, say N/A.
   
Context:
{context}

Question:
{question}

Answer:"""

    prompt = PromptTemplate.from_template(template)
    formatted_output = output_format.lower().strip()

    try:
        if formatted_output == "json":
            response_model = create_response_model_from_schema(schema)
            structured_output_method: Any = getattr(llm, "with_structured_output")
            structured_llm: Any = structured_output_method(response_model)
            chain: Any = (
                {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
                | prompt
                | structured_llm
            )
            result = chain.invoke({"context": context, "question": question})
            if isinstance(result, dict):
                result_dict: Dict[str, Any] = cast(Dict[str, Any], result)
                answer = result_dict.get("answer", str(result_dict))
            else:
                answer = str(result)
            return str(answer).strip()

       
        plain_chain: Any = cast(
            Any,
            {
                "context": RunnablePassthrough(),
                "question": RunnablePassthrough(),
            }
            | prompt
            | llm
            | StrOutputParser(),
        )
        answer = plain_chain.invoke({"context": context, "question": question})
        return str(answer).strip()
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        print(f"Error generating answer: {e}")
        traceback.print_exc()
        return f"Error generating answer: {str(e)}"
