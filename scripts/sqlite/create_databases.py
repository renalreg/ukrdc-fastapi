import os

from ukrdc_fastapi.config import settings
from ukrdc_fastapi.dependencies.database import users_session
from ukrdc_fastapi.models.users import Base as UsersBase

if __name__ == "__main__":
    if not os.path.exists(settings.sqlite_data_dir):
        os.makedirs(settings.sqlite_data_dir)

    with users_session() as usersdb:
        engine = usersdb.get_bind()
        UsersBase.metadata.create_all(engine)
