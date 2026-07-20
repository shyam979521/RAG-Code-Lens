"""Session authentication helpers shared by protected routes."""

from functools import wraps

from flask import redirect, session, url_for


def login_required(view):
    """Redirect visitors without an authenticated session to sign in."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", error="Please sign in to access this page."))
        return view(*args, **kwargs)

    return wrapped_view
