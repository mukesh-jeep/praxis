
import os
import base64
from typing import TypedDict

from dotenv import load_dotenv
from groq import Groq
from google import genai
from google.genai import types as genai_types
from langgraph.graph import StateGraph, END

load_dotenv()

# ── Groq client (text) ────────────────────────────────────────────────────────

_groq: Groq | None = None


def _get_groq() -> Groq:
    global _groq
    if _groq is None:
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )
        _groq = Groq(api_key=api_key)
    return _groq


# ── Gemini client (vision) ────────────────────────────────────────────────────

_gemini_client: genai.Client | None = None


def _get_gemini() -> genai.Client:
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY is not set. "
            "Get a free key at https://aistudio.google.com/app/apikey "
            "and add it to your .env file."
        )
    _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


# ── LLM call helpers ──────────────────────────────────────────────────────────

TEXT_MODEL   = "llama-3.3-70b-versatile"   # Groq — best free text model
VISION_MODEL = "gemini-2.0-flash"           # Google — best free vision model


def _chat_text(messages: list) -> str:
    """Groq text completion — handles text + document turns."""
    client = _get_groq()
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""


def _chat_vision(messages: list) -> str:
    """
    Gemini 2.0 Flash vision completion (google-genai SDK).

    Converts the OpenAI-format multimodal message list into Gemini's
    content format, combining system context with the user's image + text.
    """
    client = _get_gemini()

    # ── Build Gemini content parts ────────────────────────────────────────────
    parts: list = []

    for msg in messages:
        if msg["role"] == "system":
            parts.append(msg["content"])
        elif msg["role"] == "user":
            content = msg["content"]
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if item["type"] == "text":
                        parts.append(item["text"])
                    elif item["type"] == "image_url":
                        # Extract base64 data URI → raw bytes
                        data_uri = item["image_url"]["url"]
                        header, b64data = data_uri.split(",", 1)
                        mime = header.split(":")[1].split(";")[0]
                        img_bytes = base64.b64decode(b64data)
                        parts.append(
                            genai_types.Part.from_bytes(
                                data=img_bytes, mime_type=mime
                            )
                        )

    response = client.models.generate_content(
        model=VISION_MODEL,
        contents=parts,
    )
    return response.text or ""


def _is_vision_turn(messages: list) -> bool:
    """True if the last user message contains an image."""
    for msg in reversed(messages):
        if msg["role"] == "user":
            content = msg["content"]
            if isinstance(content, list):
                return any(
                    item.get("type") == "image_url" for item in content
                )
            return False
    return False


# ── Graph state ───────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: list
    answer: str
    is_medical: bool


# ── Nodes ─────────────────────────────────────────────────────────────────────

def classify_node(state: AgentState) -> AgentState:
    """Quick single-turn call to decide medical vs off-topic."""
    # Extract last user text for classification
    query = ""
    for msg in reversed(state["messages"]):
        if msg["role"] == "user":
            content = msg["content"]
            if isinstance(content, str):
                query = content
            elif isinstance(content, list):
                for part in content:
                    if part.get("type") == "text":
                        query = part["text"]
                        break
            break

    # Vision queries (images) are always treated as medical to avoid
    # the small classify call burning a Gemini API call
    if _is_vision_turn(state["messages"]):
        return {**state, "is_medical": True}

    classification_prompt = [
        {
            "role": "system",
            "content": (
                "You are a classifier. Reply with exactly 'MEDICAL' if the input "
                "is a medical question, or 'GENERAL' if it is not. No other words."
            ),
        },
        {"role": "user", "content": query[:500]},
    ]
    result = _chat_text(classification_prompt)
    return {**state, "is_medical": "MEDICAL" in result.upper()}


def generate_node(state: AgentState) -> AgentState:
    """Route to Gemini (vision) or Groq (text) and generate an answer."""
    if _is_vision_turn(state["messages"]):
        answer = _chat_vision(state["messages"])
    else:
        answer = _chat_text(state["messages"])
    return {**state, "answer": answer}


def general_node(state: AgentState) -> AgentState:
    """Polite redirect for off-topic queries; still uses any uploaded context."""
    redirect_messages = [
        {
            "role": "system",
            "content": (
                "You are a medical assistant. The user asked an off-topic question. "
                "Gently remind them you specialise in medical topics, but try to help "
                "if you can from the provided context."
            ),
        },
        *state["messages"][1:],
    ]
    return {**state, "answer": _chat_text(redirect_messages)}


def verify_node(state: AgentState) -> AgentState:
    """Append a disclaimer if no explicit source citation is found."""
    answer = state["answer"]
    has_citation = "[KB-" in answer or "[Uploaded document]" in answer

    if not has_citation and state.get("is_medical", True):
        answer += (
            "\n\n---\n*This answer was generated from the provided context. "
            "If knowledge-base chunks were not retrieved, this may draw on the "
            "model's training data — always verify with a qualified medical source.*"
        )
    return {**state, "answer": answer}


# ── Routing ───────────────────────────────────────────────────────────────────

def route_after_classify(state: AgentState) -> str:
    return "generate" if state["is_medical"] else "general"


# ── Build & compile graph ─────────────────────────────────────────────────────

_workflow = StateGraph(AgentState)
_workflow.add_node("classify", classify_node)
_workflow.add_node("generate", generate_node)
_workflow.add_node("general",  general_node)
_workflow.add_node("verify",   verify_node)

_workflow.set_entry_point("classify")
_workflow.add_conditional_edges(
    "classify", route_after_classify,
    {"generate": "generate", "general": "general"},
)
_workflow.add_edge("generate", "verify")
_workflow.add_edge("general",  "verify")
_workflow.add_edge("verify",   END)

_graph = _workflow.compile()


# ── Public API ────────────────────────────────────────────────────────────────

async def run_agent(messages: list) -> str:
    """Run the LangGraph agent and return the final answer string."""
    initial: AgentState = {
        "messages":   messages,
        "answer":     "",
        "is_medical": True,
    }
    final = await _graph.ainvoke(initial)
    return final["answer"]
