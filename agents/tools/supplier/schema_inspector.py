from sqlalchemy import text
from services.database import engine


def inspect_database_schema():

    query = text("""
        SELECT
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """)

    with engine.connect() as connection:
        results = connection.execute(query)

        for row in results:
            print(
                f"Table: {row.table_name} | "
                f"Column: {row.column_name} | "
                f"Type: {row.data_type}"
            )


if __name__ == "__main__":
    inspect_database_schema()
    