"""Profile onboarding utilities."""

def get_profile_onboarding_status(app, user_id: str) -> dict:
    """Get the current profile onboarding status for a user."""
    return {"completed": True, "version": 1}


def complete_profile_onboarding(app, user_id: str) -> dict:
    """Mark profile onboarding as complete."""
    return {"ok": True}
