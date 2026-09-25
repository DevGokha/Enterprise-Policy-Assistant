"""LLM service provider abstraction supporting Groq API with robust fallback."""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def is_valid_groq_key(key: str) -> bool:
    """Check if the provided key looks like an actual Groq API key (starts with gsk_ and not a dummy string)."""
    return bool(key and key.startswith("gsk_") and len(key) > 20 and "your_api_key" not in key)


def get_llm(model_name: Optional[str] = None):
    """Retrieve LangChain ChatGroq instance if valid API key is present."""
    api_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY)
    model = model_name or os.getenv("LLM_MODEL", DEFAULT_MODEL)

    if is_valid_groq_key(api_key):
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                groq_api_key=api_key,
                model_name=model,
                temperature=0.1
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatGroq: {e}")
            return None
    return None


def generate_rag_answer(context_chunks: list, question: str) -> str:
    """Generate grounded answer strictly from retrieved context chunks.
    
    If LLM API is available, calls ChatGroq with strict grounding prompt.
    If no LLM key is configured, formats a grounded response directly from the top matched context chunks.
    """
    if not context_chunks:
        return "I could not find this information in the available company policy documents."

    formatted_context = "\n\n".join([
        f"[Source: {c.get('source', 'Unknown')}, Page: {c.get('page', 1)}, Version: {c.get('policy_version', '1.0')}]\n{c.get('text', '')}"
        for c in context_chunks
    ])

    llm = get_llm()
    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            from app.agent.prompts import POLICY_RAG_SYSTEM_PROMPT, POLICY_RAG_USER_TEMPLATE

            prompt_content = POLICY_RAG_USER_TEMPLATE.format(
                context=formatted_context,
                question=question
            )
            messages = [
                SystemMessage(content=POLICY_RAG_SYSTEM_PROMPT),
                HumanMessage(content=prompt_content)
            ]
            response = llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.warning(f"Groq API call encountered error: {e}. Falling back to deterministic context answer.")

    # Resilient fallback: ground directly on the top retrieved chunk
    top_chunk = context_chunks[0]
    src = top_chunk.get("source", "policy document")
    pg = top_chunk.get("page", 1)
    text_snippet = top_chunk.get("text", "").strip()

    # Create grounded summary
    first_two_lines = "\n".join(text_snippet.splitlines()[:4])
    return (
        f"According to the official {top_chunk.get('document_type', 'Policy')} ({src}, Page {pg}):\n\n"
        f"{first_two_lines}\n\n"
        f"Source: {src}, Page {pg}"
    )
