"""
config.py — loads environment variables and Portfolio_Guidelines from Google Sheets.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class Config:
    # Google Sheets
    google_sheets_id: str = field(default_factory=lambda: _require("GOOGLE_SHEETS_ID"))
    google_service_account_json: str = field(
        default_factory=lambda: _require("GOOGLE_SERVICE_ACCOUNT_JSON")
    )

    # Gemini
    gemini_api_key: str = field(default_factory=lambda: _require("GEMINI_API_KEY"))

    # AMFI
    amfi_base_url: str = field(
        default_factory=lambda: os.getenv(
            "AMFI_BASE_URL", "https://www.amfiindia.com/spages/NAVAll.txt"
        )
    )

    # Scheduler
    run_hour: int = field(default_factory=lambda: int(os.getenv("RUN_HOUR", "8")))
    run_minute: int = field(default_factory=lambda: int(os.getenv("RUN_MINUTE", "0")))
    timezone: str = field(default_factory=lambda: os.getenv("TIMEZONE", "Asia/Kolkata"))

    # Portfolio guidelines — loaded from Sheets at runtime
    guidelines: dict[str, Any] = field(default_factory=dict)

    def load_guidelines(self, sheets_client: Any) -> None:
        """Fetch Portfolio_Guidelines tab from Google Sheets and populate self.guidelines."""
        try:
            result = (
                sheets_client.spreadsheets()
                .values()
                .get(spreadsheetId=self.google_sheets_id, range="Portfolio_Guidelines!A:B")
                .execute()
            )
            rows = result.get("values", [])
            self.guidelines = {row[0]: row[1] for row in rows if len(row) >= 2}
            logger.info("Loaded %d guideline entries from Portfolio_Guidelines tab.", len(self.guidelines))
        except Exception:
            logger.exception("Failed to load Portfolio_Guidelines from Sheets.")
            raise


def _require(var: str) -> str:
    value = os.getenv(var)
    if not value:
        raise EnvironmentError(f"Required environment variable '{var}' is not set.")
    return value


def load_config() -> Config:
    return Config()
