from sqlalchemy import func, select
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.selectable import Select


def count_rows(stmt: Select, session: Session) -> int:
    # Create a subquery from the select statement
    subquery = stmt.alias()

    # Create a new select statement that selects the count of rows from the subquery
    stmt_count = select(func.count()).select_from(subquery)

    # Execute the count statement and fetch the count
    count = session.execute(stmt_count).scalar_one()

    return count
