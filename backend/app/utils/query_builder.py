"""
Google Drive Query Builder Utility.

Provides a fluent interface for constructing valid Drive API `q` parameter
strings. This is used by both the LangChain tool and the Drive service to
compose complex, combinatorial queries safely.

Reference: https://developers.google.com/drive/api/guides/search-files
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class MimeType(str, Enum):
    """Common Google Drive / Google Workspace MIME types."""

    DOCUMENT = "application/vnd.google-apps.document"
    SPREADSHEET = "application/vnd.google-apps.spreadsheet"
    PRESENTATION = "application/vnd.google-apps.presentation"
    FOLDER = "application/vnd.google-apps.folder"
    PDF = "application/pdf"
    IMAGE_PNG = "image/png"
    IMAGE_JPEG = "image/jpeg"
    CSV = "text/csv"
    PLAIN_TEXT = "text/plain"
    WORD = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    POWERPOINT = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ZIP = "application/zip"


# ── Friendly name → MIME type mapping used by the LLM agent ─────────────
FILE_TYPE_MAP: dict[str, list[str]] = {
    "document": [MimeType.DOCUMENT, MimeType.WORD, MimeType.PLAIN_TEXT],
    "spreadsheet": [MimeType.SPREADSHEET, MimeType.EXCEL, MimeType.CSV],
    "presentation": [MimeType.PRESENTATION, MimeType.POWERPOINT],
    "pdf": [MimeType.PDF],
    "image": [MimeType.IMAGE_PNG, MimeType.IMAGE_JPEG],
    "folder": [MimeType.FOLDER],
}


@dataclass
class DriveQueryBuilder:
    """
    Fluent builder for Google Drive API search queries.

    Usage:
        q = (
            DriveQueryBuilder()
            .name_contains("budget")
            .mime_type("application/pdf")
            .modified_after("2024-01-01")
            .full_text("quarterly review")
            .in_folder("abc123")
            .not_trashed()
            .build()
        )
    """

    _clauses: List[str] = field(default_factory=list)

    # ── Name filters ─────────────────────────────────────────────────────

    def name_contains(self, text: str) -> "DriveQueryBuilder":
        """Add a `name contains` clause."""
        self._clauses.append(f"name contains '{self._escape(text)}'")
        return self

    def name_equals(self, text: str) -> "DriveQueryBuilder":
        """Add a `name =` clause for exact-name matching."""
        self._clauses.append(f"name = '{self._escape(text)}'")
        return self

    # ── MIME type ────────────────────────────────────────────────────────

    def mime_type(self, mime: str) -> "DriveQueryBuilder":
        """Filter to a specific MIME type."""
        self._clauses.append(f"mimeType = '{self._escape(mime)}'")
        return self

    def mime_types(self, mimes: list[str]) -> "DriveQueryBuilder":
        """Filter to any of several MIME types (OR'd together)."""
        if len(mimes) == 1:
            return self.mime_type(mimes[0])
        parts = " or ".join(
            f"mimeType = '{self._escape(m)}'" for m in mimes
        )
        self._clauses.append(f"({parts})")
        return self

    # ── Date filters ─────────────────────────────────────────────────────

    def modified_after(self, iso_date: str) -> "DriveQueryBuilder":
        """Files modified after a given ISO-8601 date string."""
        dt = self._normalise_date(iso_date)
        self._clauses.append(f"modifiedTime > '{dt}'")
        return self

    def modified_before(self, iso_date: str) -> "DriveQueryBuilder":
        """Files modified before a given ISO-8601 date string."""
        dt = self._normalise_date(iso_date)
        self._clauses.append(f"modifiedTime < '{dt}'")
        return self

    # ── Full-text content search ─────────────────────────────────────────

    def full_text(self, text: str) -> "DriveQueryBuilder":
        """Full-text content search across file bodies."""
        self._clauses.append(f"fullText contains '{self._escape(text)}'")
        return self

    # ── Folder scoping ───────────────────────────────────────────────────

    def in_folder(self, folder_id: str) -> "DriveQueryBuilder":
        """Restrict search to a specific parent folder."""
        self._clauses.append(f"'{self._escape(folder_id)}' in parents")
        return self

    # ── Trash filter ─────────────────────────────────────────────────────

    def not_trashed(self) -> "DriveQueryBuilder":
        """Exclude trashed files."""
        self._clauses.append("trashed = false")
        return self

    # ── Build ────────────────────────────────────────────────────────────

    def build(self) -> str:
        """
        Combine all clauses with `and` and return the final query string.

        Returns an empty string if no clauses were added.
        """
        return " and ".join(self._clauses)

    # ── Internals ────────────────────────────────────────────────────────

    @staticmethod
    def _escape(value: str) -> str:
        """Escape single quotes for the Drive API query syntax."""
        return value.replace("\\", "\\\\").replace("'", "\\'")

    @staticmethod
    def _normalise_date(date_str: str) -> str:
        """
        Accept various date formats and return a Drive-API-compatible
        RFC 3339 datetime string.
        """
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                continue
        # If nothing matched, return as-is and let the API handle it
        return date_str


def build_query_from_params(
    *,
    name_contains: Optional[str] = None,
    name_equals: Optional[str] = None,
    file_type: Optional[str] = None,
    mime_type: Optional[str] = None,
    modified_after: Optional[str] = None,
    modified_before: Optional[str] = None,
    full_text: Optional[str] = None,
    folder_id: Optional[str] = None,
    include_trashed: bool = False,
) -> str:
    """
    Convenience function that builds a Drive query from keyword arguments.

    This is the primary interface used by the LangChain tool.
    """
    qb = DriveQueryBuilder()

    if name_equals:
        qb.name_equals(name_equals)
    elif name_contains:
        qb.name_contains(name_contains)

    if file_type:
        friendly = file_type.lower().strip()
        mimes = FILE_TYPE_MAP.get(friendly)
        if mimes:
            qb.mime_types(mimes)
    elif mime_type:
        qb.mime_type(mime_type)

    if modified_after:
        qb.modified_after(modified_after)
    if modified_before:
        qb.modified_before(modified_before)
    if full_text:
        qb.full_text(full_text)
    if folder_id:
        qb.in_folder(folder_id)
    if not include_trashed:
        qb.not_trashed()

    return qb.build()
