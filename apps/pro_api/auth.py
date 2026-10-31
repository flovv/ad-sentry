from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("pmax_sentry.pro_api")


def mask_sensitive_data(text: str) -> str:
    """
    Sanitizes log messages by masking customer IDs (10 digits) and potential token secrets.
    """
    # Mask 10-digit customer ids: 1234567890 -> 123****890
    text = re.sub(r"\b(\d{3})\d{4}(\d{3})\b", r"\1****\2", text)
    # Mask bearer tokens
    text = re.sub(r"(Bearer\s+)[A-Za-z0-9_\-\.]{10,}", r"\1[MASKED]", text)
    return text


class MaskingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        orig = super().format(record)
        return mask_sensitive_data(orig)
