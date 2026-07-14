"""Phone number validation and normalization utilities."""

import re

# China mobile phone regex (simple)
_CN_MOBILE_RE = re.compile(r'^1[3-9]\d{9}$')


def is_valid_sms_mobile(phone: str) -> bool:
    """Check if a phone number is valid for SMS delivery."""
    if not phone:
        return False
    # Remove common prefixes
    cleaned = phone.strip().lstrip('+').lstrip('86')
    if cleaned.startswith('0'):
        cleaned = cleaned[1:]
    return bool(_CN_MOBILE_RE.match(cleaned))


def normalize_phone_identifier(phone: str) -> str:
    """Normalize a phone number to a canonical identifier for lookups."""
    if not phone:
        return ''
    cleaned = phone.strip().lstrip('+').lstrip('86')
    if cleaned.startswith('0'):
        cleaned = cleaned[1:]
    return cleaned
