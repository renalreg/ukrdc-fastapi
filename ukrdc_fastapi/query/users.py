from sqlalchemy import exc
from sqlalchemy.orm.session import Session

from ukrdc_fastapi.dependencies.auth import UKRDCUser
from ukrdc_fastapi.models.users import UserPreference
from ukrdc_fastapi.schemas.user import UserPreferences, UserPreferencesRequest


def get_user_preferences(usersdb: Session, user: UKRDCUser) -> UserPreferences:
    """
    Read current user preferences from the database, including default values where
    none have been explicitly set.

    Args:
        usersdb (Session): User info database session
        user (UKRDCUser): Logged-in user

    Returns:
        ReadUserPreferences: User preferences
    """
    all_prefs = (
        usersdb.query(UserPreference).filter(UserPreference.uid == user.id).all()
    )
    raw_prefs_dict = {row.key: row.val for row in all_prefs}
    return UserPreferences(**raw_prefs_dict)


def update_user_preferences(
    usersdb: Session, user: UKRDCUser, prefs: UserPreferencesRequest
) -> UserPreferences:
    """Update user preferences database

    Args:
        usersdb (Session): User info database session
        user (UKRDCUser): Logged-in user
        prefs (UpdateUserPreferences): New user preferences

    Returns:
        ReadUserPreferences: User preferences
    """
    try:
        # For each explicitly-included preference key-value pair
        for key, val in prefs.dict(exclude_unset=True).items():
            # Create and merge a new database row
            usersdb.merge(UserPreference(uid=user.id, key=key, val=val))
        usersdb.commit()
    except exc.SQLAlchemyError as e:
        # Rollback on error, and re-raise
        usersdb.rollback()
        raise e

    # Return full preferences object
    return get_user_preferences(usersdb, user)
