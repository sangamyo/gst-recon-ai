"""Centralized logging using Loguru."""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from app.config import get_settings

_settings = get_settings()
log_path = Path(_settings.storage_dir) / "logs"
try:
    log_path.mkdir(parents=True, exist_ok=True)
    logger.add(log_path / "gst_recon.log", rotation="10 MB", retention="14 days")
except OSError:  # pragma: no cover - read-only filesystem: stdout logging only
    logger.warning("Could not create log directory {}; logging to stderr only", log_path)

__all__ = ["logger"]
