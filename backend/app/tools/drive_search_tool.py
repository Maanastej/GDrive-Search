"""
Drive Search Tool — LangChain tool for searching Google Drive.

This is the ONLY interface the LLM agent uses to interact with Drive.
It accepts structured search parameters, builds a Drive API query via
the QueryBuilder, executes it through the GoogleDriveService, and
returns a formatted string the LLM can reason over.
"""

from __future__ import annotations

import json
from typing import Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.drive_service import GoogleDriveService
from app.utils.logger import get_logger
from app.utils.query_builder import build_query_from_params

logger = get_logger(__name__)


# ── Tool Input Schema ────────────────────────────────────────────────────

class DriveSearchInput(BaseModel):
    """Input schema for the DriveSearchTool — consumed by the LLM via function calling."""

    name_contains: Optional[str] = Field(
        default=None,
        description="Partial filename to search for (e.g. 'budget', 'report').",
    )
    name_equals: Optional[str] = Field(
        default=None,
        description="Exact filename to search for (e.g. 'Q4 Report.pdf').",
    )
    file_type: Optional[str] = Field(
        default=None,
        description=(
            "Friendly file type name. "
            "Options: document, spreadsheet, presentation, pdf, image, folder."
        ),
    )
    mime_type: Optional[str] = Field(
        default=None,
        description="Specific MIME type (e.g. 'application/pdf'). Use file_type instead when possible.",
    )
    modified_after: Optional[str] = Field(
        default=None,
        description="ISO-8601 date string — return files modified after this date (e.g. '2024-06-01').",
    )
    modified_before: Optional[str] = Field(
        default=None,
        description="ISO-8601 date string — return files modified before this date.",
    )
    full_text: Optional[str] = Field(
        default=None,
        description="Search inside file contents for this text (e.g. 'quarterly revenue').",
    )
    page_size: Optional[int] = Field(
        default=None,
        description="Number of results to return (default 20, max 50).",
    )
    folder_id: Optional[str] = Field(
        default=None,
        description="Optional ID of a specific folder to search within (non-recursive top-level search).",
    )


# ── Tool Implementation ─────────────────────────────────────────────────

class DriveSearchTool(BaseTool):
    """
    Search files in Google Drive.

    Accepts natural-language-derived parameters, builds a Drive API query,
    executes it, and returns formatted results the LLM can present to the user.
    """

    name: str = "drive_search"
    description: str = (
        "Search for files in Google Drive. Provide search parameters such as "
        "name_contains, file_type, modified_after, full_text, etc. "
        "Returns a list of matching files with metadata."
    )
    args_schema: Type[BaseModel] = DriveSearchInput

    # Injected dependency
    drive_service: GoogleDriveService = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(
        self,
        name_contains: Optional[str] = None,
        name_equals: Optional[str] = None,
        file_type: Optional[str] = None,
        mime_type: Optional[str] = None,
        modified_after: Optional[str] = None,
        modified_before: Optional[str] = None,
        full_text: Optional[str] = None,
        page_size: Optional[int] = None,
        folder_id: Optional[str] = None,
    ) -> str:
        """Execute the Drive search synchronously and return formatted results."""
        try:
            # 1) Build the query string
            query = build_query_from_params(
                name_contains=name_contains,
                name_equals=name_equals,
                file_type=file_type,
                mime_type=mime_type,
                modified_after=modified_after,
                modified_before=modified_before,
                full_text=full_text,
                folder_id=folder_id,
            )

            logger.info(
                "DriveSearchTool called — query=%s, page_size=%s",
                query,
                page_size,
            )

            # 2) Execute via the Drive service
            result = self.drive_service.search_files(
                query=query,
                page_size=page_size,
            )

            # 3) Format the result for the LLM
            if not result.files:
                return json.dumps(
                    {
                        "status": "no_results",
                        "query_used": result.query_used,
                        "message": "No files matched the search criteria.",
                        "files": [],
                    },
                    indent=2,
                )

            files_data = []
            for f in result.files:
                files_data.append(
                    {
                        "name": f.name,
                        "type": f.friendly_type,
                        "modified": f.modified_time or "Unknown",
                        "size": f.friendly_size,
                        "link": f.web_view_link or "No link available",
                        "id": f.id,
                    }
                )

            return json.dumps(
                {
                    "status": "success",
                    "query_used": result.query_used,
                    "total_count": result.total_count,
                    "files": files_data,
                    "has_more": result.next_page_token is not None,
                },
                indent=2,
            )

        except Exception as exc:
            logger.exception("DriveSearchTool error")
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Search failed: {str(exc)}",
                    "files": [],
                }
            )

    async def _arun(self, **kwargs) -> str:
        """Async variant — delegates to sync for simplicity."""
        return self._run(**kwargs)
