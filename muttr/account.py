"""Local account model with placeholder auth flow."""

import json
import os

from muttr.config import APP_SUPPORT_DIR

ACCOUNT_PATH = os.path.join(APP_SUPPORT_DIR, "account.json")

ACCOUNT_DEFAULTS = {
    "email": "",
    "display_name": "",
    "signed_in": False,
    "preferences": {
        "auto_copy": True,
        "sound_feedback": False,
        "show_overlay": True,
    },
}


def load_account():
    """Load account data from disk."""
    data = dict(ACCOUNT_DEFAULTS)
    data["preferences"] = dict(ACCOUNT_DEFAULTS["preferences"])
    if os.path.exists(ACCOUNT_PATH):
        try:
            with open(ACCOUNT_PATH, "r") as f:
                stored = json.load(f)
            data.update(stored)
            if "preferences" in stored:
                merged_prefs = dict(ACCOUNT_DEFAULTS["preferences"])
                merged_prefs.update(stored["preferences"])
                data["preferences"] = merged_prefs
        except (json.JSONDecodeError, OSError):
            pass
    return data


def save_account(data):
    """Persist account data and notify listeners."""
    os.makedirs(APP_SUPPORT_DIR, exist_ok=True)
    with open(ACCOUNT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    from muttr import events
    events.emit("account_changed", account=data)


def sign_in(email, display_name=""):
    """Placeholder sign-in. Stores locally; wire to a real backend later."""
    account = load_account()
    account["email"] = email
    account["display_name"] = display_name or email.split("@")[0]
    account["signed_in"] = True
    save_account(account)
    return account


def sign_out():
    """Clear sign-in state."""
    account = load_account()
    account["signed_in"] = False
    save_account(account)
    return account


def update_preferences(prefs):
    """Merge preference updates."""
    account = load_account()
    account["preferences"].update(prefs)
    save_account(account)
    return account
