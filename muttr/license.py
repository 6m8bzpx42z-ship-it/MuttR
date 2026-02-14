"""License key parsing, validation, and storage.

License key format: MUTTR-{tier}-{expiry_ts}-{hmac_signature}
Tiers: standard, unlimited, lifetime
Expiry: Unix timestamp (0 for lifetime)
Signature: HMAC-SHA256 of "MUTTR-{tier}-{expiry}" using shared secret
"""

import hashlib
import hmac
import os
import subprocess
import time

from muttr.config import APP_SUPPORT_DIR

# Shared secret for HMAC validation (embedded in app)
# In production, this would be obfuscated or fetched from a secure source
_HMAC_SECRET = b"muttr-launch-2026-hmac-secret-key"

# Tier constants
TIER_FREE = "free"
TIER_STANDARD = "standard"
TIER_UNLIMITED = "unlimited"
TIER_LIFETIME = "lifetime"

# Word limits per tier (daily)
_WORD_LIMITS = {
    TIER_FREE: 500,
    TIER_STANDARD: 1000,
    TIER_UNLIMITED: None,  # unlimited
    TIER_LIFETIME: None,   # unlimited
}

_KEYCHAIN_SERVICE = "MuttR"
_KEYCHAIN_ACCOUNT = "license-key"


def _store_in_keychain(key: str) -> None:
    """Store license key in macOS Keychain."""
    # Delete existing entry first (ignore errors if not found)
    subprocess.run(
        ["security", "delete-generic-password", "-s", _KEYCHAIN_SERVICE,
         "-a", _KEYCHAIN_ACCOUNT],
        capture_output=True,
    )
    subprocess.run(
        ["security", "add-generic-password", "-s", _KEYCHAIN_SERVICE,
         "-a", _KEYCHAIN_ACCOUNT, "-w", key],
        capture_output=True, check=True,
    )


def _load_from_keychain() -> str | None:
    """Load license key from macOS Keychain."""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", _KEYCHAIN_SERVICE,
         "-a", _KEYCHAIN_ACCOUNT, "-w"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _compute_signature(tier: str, expiry: str) -> str:
    """Compute HMAC-SHA256 signature for a license key."""
    message = f"MUTTR-{tier}-{expiry}".encode()
    return hmac.new(_HMAC_SECRET, message, hashlib.sha256).hexdigest()[:16]


def validate_key(key: str) -> dict | None:
    """Parse and validate a license key.

    Returns dict with {tier, expiry, valid} or None if invalid format.
    """
    parts = key.strip().split("-")
    if len(parts) != 4 or parts[0] != "MUTTR":
        return None

    _, tier, expiry_str, signature = parts

    if tier not in (TIER_STANDARD, TIER_UNLIMITED, TIER_LIFETIME):
        return None

    # Verify HMAC signature
    expected_sig = _compute_signature(tier, expiry_str)
    if not hmac.compare_digest(signature, expected_sig):
        return None

    # Check expiry (35-day grace period built into key generation)
    try:
        expiry = int(expiry_str)
    except ValueError:
        return None

    if tier == TIER_LIFETIME:
        expired = False
    else:
        expired = expiry > 0 and time.time() > expiry

    return {
        "tier": tier,
        "expiry": expiry,
        "valid": not expired,
    }


def activate(key: str) -> dict | None:
    """Validate and store a license key. Returns validation result."""
    result = validate_key(key)
    if result and result["valid"]:
        _store_in_keychain(key)
    return result


def get_tier() -> str:
    """Return the current license tier."""
    key = _load_from_keychain()
    if not key:
        return TIER_FREE

    result = validate_key(key)
    if result and result["valid"]:
        return result["tier"]
    return TIER_FREE


def get_daily_word_limit() -> int | None:
    """Return the daily word limit for the current tier, or None for unlimited."""
    tier = get_tier()
    return _WORD_LIMITS.get(tier, 500)


def is_licensed() -> bool:
    """Return True if the user has an active paid license."""
    return get_tier() != TIER_FREE


def deactivate() -> None:
    """Remove the stored license key."""
    subprocess.run(
        ["security", "delete-generic-password", "-s", _KEYCHAIN_SERVICE,
         "-a", _KEYCHAIN_ACCOUNT],
        capture_output=True,
    )
