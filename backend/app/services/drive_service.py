"""
Google Drive Service.

Encapsulates all Google Drive API interactions behind a clean service
interface. Handles authentication, query execution, pagination, and
response normalisation.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import get_settings
from app.models.schemas import DriveFile, SearchResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Scopes required for read-only Drive access
_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class GoogleDriveService:
    """
    Service layer for Google Drive API operations.

    Authenticates via a service account and exposes high-level search
    methods that return typed domain models.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._service = self._build_service()
        logger.info("GoogleDriveService initialised")

    # ── Authentication ───────────────────────────────────────────────────

    def _build_service(self):
        """
        Authenticate with Google and return a Drive API service object.

        Supports two credential sources:
        1. A JSON file path  (GOOGLE_SERVICE_ACCOUNT_FILE)
        2. Raw JSON in an env var  (GOOGLE_SERVICE_ACCOUNT_JSON) — useful for
           Railway / Render where you paste the JSON into a secret.
        """
        raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

        if raw_json:
            info = json.loads(raw_json)
            credentials = service_account.Credentials.from_service_account_info(
                info, scopes=_SCOPES
            )
            logger.info("Authenticated via GOOGLE_SERVICE_ACCOUNT_JSON env var")
        else:
            sa_file = self._settings.GOOGLE_SERVICE_ACCOUNT_FILE
            if not os.path.exists(sa_file):
                raise FileNotFoundError(
                    f"Service account file not found: {sa_file}. "
                    "Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON."
                )
            credentials = service_account.Credentials.from_service_account_file(
                sa_file, scopes=_SCOPES
            )
            logger.info("Authenticated via service account file: %s", sa_file)

        return build("drive", "v3", credentials=credentials, cache_discovery=False)

    # ── Public API ───────────────────────────────────────────────────────

    def search_files(
        self,
        query: str,
        page_size: Optional[int] = None,
        page_token: Optional[str] = None,
        order_by: str = "modifiedTime desc",
    ) -> SearchResult:
        """
        Execute a Drive API files.list call with the given `q` parameter.

        Args:
            query:      Drive API query string (built by QueryBuilder).
            page_size:  Number of results per page.
            page_token: Token for the next page of results.
            order_by:   Sort order — defaults to most recently modified first.

        Returns:
            A SearchResult containing typed DriveFile objects.
        """
        page_size = page_size or self._settings.DRIVE_PAGE_SIZE

        # Scope to a specific folder if configured
        folder_id = self._settings.GOOGLE_DRIVE_FOLDER_ID
        if folder_id and f"in parents" not in query:
            folder_clause = f"'{folder_id}' in parents"
            query = f"{query} and {folder_clause}" if query else folder_clause

        logger.info("Drive query: %s", query)

        try:
            request_params: Dict[str, Any] = {
                "q": query,
                "pageSize": min(page_size, self._settings.DRIVE_MAX_RESULTS),
                "fields": (
                    "nextPageToken, "
                    "files(id, name, mimeType, webViewLink, webContentLink, "
                    "iconLink, modifiedTime, size, owners)"
                ),
                "orderBy": order_by,
                "supportsAllDrives": True,
                "includeItemsFromAllDrives": True,
            }
            if page_token:
                request_params["pageToken"] = page_token

            response = (
                self._service.files()
                .list(**request_params)
                .execute()
            )

            raw_files = response.get("files", [])
            files = [DriveFile(**f) for f in self._normalise_files(raw_files)]

            result = SearchResult(
                files=files,
                total_count=len(files),
                query_used=query,
                next_page_token=response.get("nextPageToken"),
            )
            logger.info("Found %d file(s)", result.total_count)
            return result

        except HttpError as exc:
            logger.error("Drive API error: %s", exc)
            raise RuntimeError(f"Google Drive API error: {exc}") from exc

    def get_file_metadata(self, file_id: str) -> DriveFile:
        """Fetch full metadata for a single file."""
        try:
            meta = (
                self._service.files()
                .get(
                    fileId=file_id,
                    fields=(
                        "id, name, mimeType, webViewLink, webContentLink, "
                        "iconLink, modifiedTime, size, owners"
                    ),
                    supportsAllDrives=True,
                )
                .execute()
            )
            normalised = self._normalise_files([meta])[0]
            return DriveFile(**normalised)
        except HttpError as exc:
            logger.error("Drive API error fetching file %s: %s", file_id, exc)
            raise RuntimeError(f"Could not fetch file {file_id}: {exc}") from exc

    # ── Internal helpers ─────────────────────────────────────────────────

    @staticmethod
    def _normalise_files(raw_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalise Drive API camelCase keys to snake_case for Pydantic.
        """
        normalised = []
        for f in raw_files:
            normalised.append(
                {
                    "id": f.get("id", ""),
                    "name": f.get("name", "Untitled"),
                    "mime_type": f.get("mimeType", "unknown"),
                    "web_view_link": f.get("webViewLink"),
                    "web_content_link": f.get("webContentLink"),
                    "icon_link": f.get("iconLink"),
                    "modified_time": f.get("modifiedTime"),
                    "size": f.get("size"),
                    "owners": f.get("owners"),
                }
            )
        return normalised
