"""LLM service provider abstraction supporting Groq API, translation, and robust fallback."""

import os
import logging
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# In-memory translation cache to avoid repeated requests and latency
_TRANSLATION_CACHE: Dict[tuple, str] = {}


def is_valid_groq_key(key: str) -> bool:
    """Check if the provided key looks like an actual Groq API key (starts with gsk_ and not a dummy string)."""
    return bool(key and key.startswith("gsk_") and len(key) > 20 and "your_api_key" not in key)


def get_llm(model_name: Optional[str] = None):
    """Retrieve LangChain ChatGroq instance if valid API key is present."""
    api_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY)
    primary_model = model_name or os.getenv("LLM_MODEL", DEFAULT_MODEL)

    if not is_valid_groq_key(api_key):
        return None

    candidate_models = [primary_model, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "llama-3.3-70b-versatile"]
    # De-duplicate while preserving order
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    from langchain_groq import ChatGroq
    for m in models_to_try:
        try:
            return ChatGroq(
                groq_api_key=api_key,
                model_name=m,
                temperature=0.1
            )
        except Exception as e:
            logger.debug(f"Could not initialize ChatGroq with model {m}: {e}")
            continue

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
        f"{first_two_lines}"
    )


def translate_text(text: str, target_lang: str) -> str:
    """Translate text into Hindi ('hi') or Marathi ('mr').
    
    Uses Groq LLM if active; otherwise utilizes deep-translator (MyMemory engine).
    Preserves formatting, bullet points, numbers, and document source citations.
    """
    if not text or not text.strip():
        return text

    # Normalize target language
    target_clean = target_lang.strip().lower()
    if target_clean in ("en", "english"):
        return text

    lang_code = "hi-IN" if target_clean in ("hi", "hindi", "हिंदी") else "mr-IN" if target_clean in ("mr", "marathi", "मराठी") else None
    if not lang_code:
        return text

    cache_key = (text.strip(), lang_code)
    if cache_key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[cache_key]

    target_name = "Hindi" if "hi" in lang_code else "Marathi"

    # Option 1: Try LLM translation if available
    llm = get_llm()
    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            sys_msg = (
                f"You are an expert enterprise translator. Translate the following English enterprise assistant response "
                f"into natural, professional {target_name}. "
                f"RULES:\n"
                f"1. Preserve all markdown formatting, asterisks, bullet points, and numbered lists.\n"
                f"2. Keep document filenames (e.g. leave_policy.pdf, wfh_policy.pdf) and page citations (e.g. Page 2) intact.\n"
                f"3. Keep employee names, request IDs (e.g. LV1025), and email addresses unchanged.\n"
                f"4. Provide ONLY the translated output without meta-commentary or conversational remarks."
            )
            response = llm.invoke([
                SystemMessage(content=sys_msg),
                HumanMessage(content=text)
            ])
            translated = response.content.strip()
            _TRANSLATION_CACHE[cache_key] = translated
            return translated
        except Exception as e:
            logger.warning(f"LLM translation failed ({e}), falling back to translation engine.")

    # Option 2: Fallback to deep-translator (MyMemory engine)
    try:
        from deep_translator import MyMemoryTranslator
        translator = MyMemoryTranslator(source='en-US', target=lang_code)
        
        # Translate line-by-line to preserve structure and formatting
        lines = text.split("\n")
        translated_lines = []
        for line in lines:
            if not line.strip() or line.strip().startswith("Source:") or line.strip().endswith(".pdf"):
                translated_lines.append(line)
            else:
                try:
                    tr = translator.translate(line)
                    translated_lines.append(tr)
                except Exception:
                    translated_lines.append(line)
                    
        result = "\n".join(translated_lines)
        _TRANSLATION_CACHE[cache_key] = result
        return result
    except Exception as e:
        logger.error(f"Fallback translation error: {e}")
        return text


def translate_to_english(text: str) -> str:
    """Translate Hindi or Marathi text to English for semantic search and intent classification."""
    if not text or not text.strip():
        return text
    # Check if text contains Devanagari characters
    has_devanagari = any('\u0900' <= char <= '\u097f' for char in text)
    if not has_devanagari:
        return text

    cache_key = ("to_en", text.strip())
    if cache_key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[cache_key]

    # Option 1: LLM translation
    llm = get_llm()
    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            response = llm.invoke([
                SystemMessage(content="Translate this Hindi/Marathi enterprise HR query into clear English. Output translation only."),
                HumanMessage(content=text)
            ])
            res = response.content.strip()
            _TRANSLATION_CACHE[cache_key] = res
            return res
        except Exception:
            pass

    # Option 2: Fallback translation
    try:
        from deep_translator import MyMemoryTranslator
        translator = MyMemoryTranslator(source='hi-IN', target='en-US')
        res = translator.translate(text)
        _TRANSLATION_CACHE[cache_key] = res
        return res
    except Exception as e:
        logger.error(f"Error translating to English: {e}")
        return text
