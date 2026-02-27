"""
hooks/pre_tool.py — Pre-tool hook: validates environment variables and credentials before each run.

Called by Claude Code before any tool execution (see hooks/.claude/hooks/).
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = [
    "GOOGLE_SHEETS_ID",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "ANTHROPIC_API_KEY",
]


def validate_environment() -> list[str]:
    """Check all required environment variables are set. Returns list of missing vars."""
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    return missing


def validate_credentials() -> list[str]:
    """Check that credential files exist and are valid JSON. Returns list of errors."""
    errors: list[str] = []
    sa_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if sa_path:
        path = Path(sa_path)
        if not path.exists():
            errors.append(f"Service account file not found: {sa_path}")
        else:
            try:
                with open(path) as f:
                    data = json.load(f)
                if "type" not in data or data["type"] != "service_account":
                    errors.append(f"File {sa_path} does not appear to be a service account JSON.")
            except json.JSONDecodeError as exc:
                errors.append(f"Service account JSON is invalid: {exc}")
    return errors


def run() -> None:
    """Run all pre-tool validations. Exits with code 1 on failure."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")

    missing_vars = validate_environment()
    if missing_vars:
        logger.error("Missing required environment variables: %s", ", ".join(missing_vars))
        logger.error("Copy .env.example to .env and fill in the values.")
        sys.exit(1)

    cred_errors = validate_credentials()
    if cred_errors:
        for err in cred_errors:
            logger.error(err)
        sys.exit(1)

    logger.info("Pre-tool validation passed.")


if __name__ == "__main__":
    run()
