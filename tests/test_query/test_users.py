from ukrdc_fastapi.models.users import UserPreference
from ukrdc_fastapi.query.users import get_user_preferences, update_user_preferences
from ukrdc_fastapi.schemas.user import UserPreferences, UserPreferencesRequest


def test_get_user_preferences_defaults(users_session, superuser):
    prefs = get_user_preferences(users_session, superuser)

    # In the absence of any manually-set preferences, ensure we get default values back
    assert prefs == UserPreferences().dict()


def test_get_user_preferences_ignores(users_session, superuser):
    # Add a database row for a nonexistent preference
    users_session.merge(UserPreference(uid=superuser.id, key="test_key", val="foo"))

    # Ensure the nonexistent preference just gets ignored
    prefs = get_user_preferences(users_session, superuser)
    assert prefs == UserPreferences().dict()


def test_update_user_preferences_placeholder(users_session, superuser):
    # Update the placeholder preference
    prefs = update_user_preferences(users_session, superuser, UserPreferencesRequest(placeholder=True))  # type: ignore

    # Ensure we get the new value back
    assert prefs.placeholder is True

    # Ensure the update preference has been committed to the database
    db_placeholder = users_session.query(UserPreference).get(
        (superuser.id, "placeholder")
    )
    assert db_placeholder
