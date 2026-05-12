"""
Drive Search Agent — LangChain conversational agent.

Orchestrates the chat flow:
  User message → LLM reasoning → Tool calling → Response formatting.

Maintains per-conversation memory so multi-turn interactions work
naturally (e.g. follow-up questions, refinements).
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.config import get_settings
from app.models.schemas import ChatResponse, DriveFile
from app.prompts.agent_prompts import get_system_prompt
from app.services.drive_service import GoogleDriveService
from app.services.llm_service import get_chat_model
from app.tools.drive_search_tool import DriveSearchTool
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DriveSearchAgent:
    """
    High-level conversational agent for Google Drive search.

    Wraps a LangChain AgentExecutor with tool-calling and per-session
    message history.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._drive_service = GoogleDriveService()
        self._llm = get_chat_model()
        self._tools = self._build_tools()
        self._agent_executor = self._build_agent()
        self._message_stores: Dict[str, InMemoryChatMessageHistory] = {}
        logger.info("DriveSearchAgent initialised with %d tool(s)", len(self._tools))

    # ── Tool setup ───────────────────────────────────────────────────────

    def _build_tools(self) -> list:
        """Instantiate all tools available to the agent."""
        drive_tool = DriveSearchTool(drive_service=self._drive_service)
        return [drive_tool]

    # ── Agent setup ──────────────────────────────────────────────────────

    def _build_agent(self) -> AgentExecutor:
        """
        Build a LangChain tool-calling agent with a conversational prompt
        and return it wrapped in an AgentExecutor.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", get_system_prompt()),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(
            llm=self._llm,
            tools=self._tools,
            prompt=prompt,
        )

        executor = AgentExecutor(
            agent=agent,
            tools=self._tools,
            verbose=self._settings.DEBUG,
            max_iterations=5,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

        return executor

    # ── Message history management ───────────────────────────────────────

    def _get_history(self, session_id: str) -> InMemoryChatMessageHistory:
        """Return (or create) a message history for the given session."""
        if session_id not in self._message_stores:
            self._message_stores[session_id] = InMemoryChatMessageHistory()
        return self._message_stores[session_id]

    def _trim_history(self, session_id: str) -> None:
        """Keep conversation history within the configured limit."""
        history = self._get_history(session_id)
        max_msgs = self._settings.MAX_CONVERSATION_HISTORY
        if len(history.messages) > max_msgs:
            history.messages = history.messages[-max_msgs:]

    # ── Public API ───────────────────────────────────────────────────────

    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Process a user message and return a ChatResponse.

        Args:
            message:         The user's natural-language query.
            conversation_id: Optional session ID for multi-turn memory.

        Returns:
            ChatResponse with the assistant's reply, any files found,
            a query explanation, and the conversation ID.
        """
        conversation_id = conversation_id or str(uuid.uuid4())
        logger.info(
            "Chat request — session=%s, message=%s",
            conversation_id,
            message[:80],
        )

        try:
            # Get session history
            history = self._get_history(conversation_id)

            # Invoke the agent
            result = await self._agent_executor.ainvoke(
                {"input": message, "chat_history": history.messages},
            )

            output_text: str = result.get("output", "I'm sorry, I couldn't process your request.")
            intermediate_steps: list = result.get("intermediate_steps", [])

            # Update conversation memory
            history.add_user_message(message)
            history.add_ai_message(output_text)
            self._trim_history(conversation_id)

            # Extract files and query explanation from intermediate steps
            files, query_explanation = self._extract_tool_results(
                intermediate_steps
            )

            return ChatResponse(
                response=output_text,
                files=files,
                query_explanation=query_explanation,
                conversation_id=conversation_id,
            )

        except Exception as exc:
            logger.exception("Agent error for session %s", conversation_id)
            return ChatResponse(
                response=(
                    "I encountered an error while processing your request. "
                    f"Details: {str(exc)}"
                ),
                files=[],
                query_explanation=None,
                conversation_id=conversation_id,
            )

    # ── Result extraction ────────────────────────────────────────────────

    @staticmethod
    def _extract_tool_results(
        intermediate_steps: list,
    ) -> tuple[List[DriveFile], Optional[str]]:
        """
        Parse intermediate steps from AgentExecutor to extract
        DriveFile objects and the query explanation.
        """
        files: List[DriveFile] = []
        query_explanation: Optional[str] = None

        for step in intermediate_steps:
            if len(step) < 2:
                continue

            action, observation = step[0], step[1]

            # observation is the JSON string returned by DriveSearchTool
            if not isinstance(observation, str):
                continue

            try:
                data = json.loads(observation)
            except (json.JSONDecodeError, TypeError):
                continue

            # Build query explanation
            query_used = data.get("query_used", "")
            if query_used:
                query_explanation = f"Drive API query: `{query_used}`"

            # Convert raw file dicts to DriveFile models
            for raw in data.get("files", []):
                try:
                    files.append(
                        DriveFile(
                            id=raw.get("id", ""),
                            name=raw.get("name", "Untitled"),
                            mime_type=raw.get("type", "unknown"),
                            web_view_link=raw.get("link"),
                            modified_time=raw.get("modified"),
                        )
                    )
                except Exception:
                    continue

        return files, query_explanation

    def clear_history(self, conversation_id: str) -> None:
        """Clear the message history for a given session."""
        if conversation_id in self._message_stores:
            del self._message_stores[conversation_id]
            logger.info("Cleared history for session %s", conversation_id)
