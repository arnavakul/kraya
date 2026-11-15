from sqlalchemy import text
from services.database import engine


def inspect_supplier_data():

    queries = {
        "SUPPLIERS": """
            SELECT *
            FROM public.suppliers
            LIMIT 5;
        """,

        "SUPPLIER CATEGORIES": """
            SELECT *
            FROM public.supplier_categories
            LIMIT 10;
        """,

        "ORGANIZATIONS": """
            SELECT
                id,
                legal_name,
                trade_name,
                organization_type,
                country_code,
                is_verified
            FROM public.organizations
            LIMIT 5;
        """,

        "SUPPLIER STATUS DISTRIBUTION": """
            SELECT status, COUNT(*)
            FROM public.suppliers
            GROUP BY status;
        """,

        "SUPPLIER CATEGORY DISTRIBUTION": """
            SELECT category, COUNT(*)
            FROM public.supplier_categories
            GROUP BY category
            ORDER BY COUNT(*) DESC;
        """
    }

    with engine.connect() as connection:

        for title, query in queries.items():

            print("\n" + "=" * 60)
            print(title)
            print("=" * 60)

            result = connection.execute(text(query))

            for row in result.mappings():
                print(dict(row))


if __name__ == "__main__":
    inspect_supplier_data()
    