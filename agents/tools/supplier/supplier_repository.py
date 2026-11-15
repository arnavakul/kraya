
from sqlalchemy import text
from services.database import engine
from pydantic_models.supplier_candidate import SupplierCandidate


class SupplierRepository:

    @staticmethod
    def get_all_suppliers(
        active_only: bool = True
    ) -> list[SupplierCandidate]:

        query = text("""
            SELECT
                s.id AS supplier_id,
                s.organization_id,
                s.name,
                s.contact_name,
                s.contact_email,
                s.contact_phone,
                s.country_code,
                s.website_url,
                s.tax_id,
                s.payment_terms,
                s.notes,
                s.status,

                o.legal_name AS organization_name,
                o.organization_type,
                o.is_verified AS organization_verified,

                COALESCE(
                    ARRAY_AGG(DISTINCT sc.category)
                    FILTER (WHERE sc.category IS NOT NULL),
                    ARRAY[]::varchar[]
                ) AS categories

            FROM public.suppliers s

            LEFT JOIN public.organizations o
                ON s.organization_id = o.id

            LEFT JOIN public.supplier_categories sc
                ON s.id = sc.supplier_id

            WHERE
                (:active_only = FALSE OR s.status = 'ACTIVE')

            GROUP BY
                s.id,
                s.organization_id,
                s.name,
                s.contact_name,
                s.contact_email,
                s.contact_phone,
                s.country_code,
                s.website_url,
                s.tax_id,
                s.payment_terms,
                s.notes,
                s.status,
                o.legal_name,
                o.organization_type,
                o.is_verified

            ORDER BY s.name;
        """)

        with engine.connect() as connection:

            results = connection.execute(
                query,
                {"active_only": active_only}
            )

            suppliers = []

            for row in results.mappings():

                supplier = SupplierCandidate(
                    **dict(row)
                )

                suppliers.append(supplier)

            return suppliers

    @staticmethod
    def get_supplier_by_id(
        supplier_id: str
    ) -> SupplierCandidate | None:

        query = text("""
            SELECT
                s.id AS supplier_id,
                s.organization_id,
                s.name,
                s.contact_name,
                s.contact_email,
                s.contact_phone,
                s.country_code,
                s.website_url,
                s.tax_id,
                s.payment_terms,
                s.notes,
                s.status,

                o.legal_name AS organization_name,
                o.organization_type,
                o.is_verified AS organization_verified,

                COALESCE(
                    ARRAY_AGG(DISTINCT sc.category)
                    FILTER (WHERE sc.category IS NOT NULL),
                    ARRAY[]::varchar[]
                ) AS categories

            FROM public.suppliers s

            LEFT JOIN public.organizations o
                ON s.organization_id = o.id

            LEFT JOIN public.supplier_categories sc
                ON s.id = sc.supplier_id

            WHERE s.id = :supplier_id

            GROUP BY
                s.id,
                s.organization_id,
                s.name,
                s.contact_name,
                s.contact_email,
                s.contact_phone,
                s.country_code,
                s.website_url,
                s.tax_id,
                s.payment_terms,
                s.notes,
                s.status,
                o.legal_name,
                o.organization_type,
                o.is_verified

        """)

        with engine.connect() as connection:

            result = connection.execute(
                query,
                {"supplier_id": supplier_id}
            ).mappings().first()

            if result is None:
                return None

            return SupplierCandidate(**dict(result))

