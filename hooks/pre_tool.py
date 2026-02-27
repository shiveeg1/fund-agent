"""
hooks/pre_tool.py — Pre-tool hook: blocks .env access and validates environment.

Claude Code calls this before every tool. The tool payload is passed via stdin as JSON.
Exit 0  → allow the tool to proceed.
Exit 2  → hard-block the tool; stdout is shown to Claude as the reason.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = [
    "GOOGLE_SHEETS_ID",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "GEMINI_API_KEY",
]

# Matches ".env" as a standalone filename — not ".env.example", ".env.local", etc.
_ENV_PATH_RE = re.compile(r"(^|[/\\])\.env$")
# Matches ".env" in a shell command (not followed by a word char or another dot+word)
_ENV_CMD_RE = re.compile(r"(?<![.\w])\.env(?!\.\w|\w)")


def _blocks_env_access(tool_name: str, tool_input: dict) -> str | None:
    """
    Return an error message if the tool would read or write the .env file, else None.
    Checked tools: Read, Edit, Write (via file_path) and Bash (via command text).
    """
    if tool_name in ("Read", "Edit", "Write"):
        path = tool_input.get("file_path", "")
        if _ENV_PATH_RE.search(path):
            return (
                f"Blocked: {tool_name} on '{path}' is not allowed. "
                "The .env file contains secrets — edit it manually in your terminal."
            )

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if _ENV_CMD_RE.search(command):
            return (
                "Blocked: shell command appears to reference the .env file. "
                "The .env file contains secrets — edit it manually in your terminal."
            )

    return None


# ---------------------------------------------------------------------------
# Standalone validation (run directly, not by Claude Code)
# ---------------------------------------------------------------------------

def validate_environment() -> list[str]:
    """Check all required environment variables are set. Returns list of missing vars."""
    return [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]


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
    logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")

    # When invoked by Claude Code, stdin is a pipe carrying the tool payload JSON.
    if not sys.stdin.isatty():
        try:
            payload = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            payload = {}

        tool_name = payload.get("tool_name", "")
        tool_input = payload.get("tool_input", {})

        error = _blocks_env_access(tool_name, tool_input)
        if error:
            print(error)
            sys.exit(2)

        sys.exit(0)

    # Standalone mode: run environment + credential checks.
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
