"""
Chat API Routes.

Provides the `/api/chat` endpoint consumed by the Streamlit frontend.
Also includes a conversation-clear endpoint for session management.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.agents.drive_agent import DriveSearchAgent
from app.models.schemas import ChatRequest, ChatResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])

# ── Singleton agent instance (created at first request) ──────────────────
_agent: DriveSearchAgent | None = None


def _get_agent() -> DriveSearchAgent:
    """Lazy-initialise the agent singleton."""
    global _agent
    if _agent is None:
        _agent = DriveSearchAgent()
    return _agent


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the Drive Search Assistant",
    description="Accepts a natural-language message and returns the assistant's response with any files found.",
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a user chat message through the LangChain agent."""
    try:
        agent = _get_agent()
        response = await agent.chat(
            message=request.message,
            conversation_id=request.conversation_id,
        )
        return response
    except Exception as exc:
        logger.exception("Chat endpoint error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your message: {str(exc)}",
        ) from exc


@router.post(
    "/clear",
    summary="Clear conversation history",
    description="Clears the message history for a given conversation ID.",
)
async def clear_conversation(conversation_id: str) -> dict:
    """Clear the conversation memory for a specific session."""
    agent = _get_agent()
    agent.clear_history(conversation_id)
    return {"status": "ok", "message": f"History cleared for {conversation_id}"}
