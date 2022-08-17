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


def test_update_user_preferences_show_ukrdc(users_session, superuser):
    # Update the search_show_ukrdc preference
    prefs = update_user_preferences(users_session, superuser, UserPreferencesRequest(search_show_ukrdc=True))  # type: ignore

    # Ensure we get the new value back
    assert prefs.search_show_ukrdc == True

    # Ensure the update preference has been committed to the database
    db_search_show_ukrdc = users_session.query(UserPreference).get(
        (superuser.id, "search_show_ukrdc")
    )
    assert db_search_show_ukrdc
