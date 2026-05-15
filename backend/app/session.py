"""
Module-level session singleton for the AI Second Brain backend.

Tracks the single active PDF session for the lifetime of the server process.
No database or persistence is used — state lives in memory only.

Functions:
    get_session()         — returns the current session state
    set_session(filename) — activates a session for the given PDF filename
    clear_session()       — deactivates the current session
"""

from app.models import SessionState

# ---------------------------------------------------------------------------
# Module-level singleton state
# ---------------------------------------------------------------------------

_session: dict = {
    "filename": None,
    "is_active": False,
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_session() -> SessionState:
    """Return the current session state as a SessionState instance."""
    return SessionState(
        filename=_session["filename"],
        is_active=_session["is_active"],
    )


def set_session(filename: str) -> None:
    """Activate a session for the given PDF filename.

    Replaces any previously active session (Requirement 1.9 / 3.5).

    Args:
        filename: The name of the PDF file that was successfully uploaded and
                  processed.
    """
    _session["filename"] = filename
    _session["is_active"] = True


def clear_session() -> None:
    """Deactivate the current session and clear the stored filename."""
    _session["filename"] = None
    _session["is_active"] = False
