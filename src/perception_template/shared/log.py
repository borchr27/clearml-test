"""Logging setup for the whole application."""

import logging


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger. Call once, at application startup."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
