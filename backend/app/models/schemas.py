"""
Pydantic schemas for API request / response payloads.

These models enforce validation at the API boundary and provide
self-documenting OpenAPI specs via FastAPI.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Request Models
# ═══════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's natural-language message.",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation ID to maintain multi-turn context.",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Domain Models
# ═══════════════════════════════════════════════════════════════════════════

class DriveFile(BaseModel):
    """Represents a single file returned from Google Drive."""

    id: str = Field(..., description="Google Drive file ID.")
    name: str = Field(..., description="File name.")
    mime_type: str = Field(..., description="MIME type of the file.")
    web_view_link: Optional[str] = Field(
        default=None, description="URL to view the file in a browser."
    )
    web_content_link: Optional[str] = Field(
        default=None, description="Direct download link (when available)."
    )
    icon_link: Optional[str] = Field(
        default=None, description="Icon representing the file type."
    )
    modified_time: Optional[str] = Field(
        default=None, description="Last modified timestamp (ISO 8601)."
    )
    size: Optional[str] = Field(
        default=None, description="File size in bytes (string)."
    )
    owners: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="List of file owners."
    )

    @property
    def friendly_type(self) -> str:
        """Return a human-readable file type label."""
        _map = {
            "application/vnd.google-apps.document": "Google Doc",
            "application/vnd.google-apps.spreadsheet": "Google Sheet",
            "application/vnd.google-apps.presentation": "Google Slides",
            "application/vnd.google-apps.folder": "Folder",
            "application/pdf": "PDF",
            "text/csv": "CSV",
            "text/plain": "Text File",
            "image/png": "PNG Image",
            "image/jpeg": "JPEG Image",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word Doc",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel Sheet",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint",
        }
        return _map.get(self.mime_type, self.mime_type.split("/")[-1].upper())

    @property
    def friendly_size(self) -> str:
        """Return a human-readable file size."""
        if not self.size:
            return "—"
        size_bytes = int(self.size)
        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"


class SearchResult(BaseModel):
    """Wrapper for search results returned by the Drive service."""

    files: List[DriveFile] = Field(default_factory=list)
    total_count: int = Field(default=0)
    query_used: str = Field(default="")
    next_page_token: Optional[str] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════════════════

class ChatResponse(BaseModel):
    """Response payload sent back to the frontend."""

    response: str = Field(
        ..., description="The assistant's natural-language reply."
    )
    files: List[DriveFile] = Field(
        default_factory=list,
        description="Files found during the search (may be empty).",
    )
    query_explanation: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of the search query built.",
    )
    conversation_id: str = Field(
        ..., description="Conversation ID for multi-turn tracking."
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Server timestamp.",
    )


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str = "ok"
    version: str = "1.0.0"
    service: str = "Drive Search Assistant"
