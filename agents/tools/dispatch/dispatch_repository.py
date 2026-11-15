
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from services.database import SessionLocal


class DuplicateDispatchError(Exception):
    """Raised when a dispatch already exists."""


class DispatchStateError(Exception):
    """Raised when a dispatch cannot transition to a requested state."""


class DispatchRepository:

    def create_dispatch(self, dispatch_data: dict) -> dict:
        session = SessionLocal()

        try:
            result = session.execute(
                text("""
                    INSERT INTO dispatch_records (
                        rfq_id,
                        recipient_email,
                        subject,
                        idempotency_key,
                        status
                    )
                    VALUES (
                        :rfq_id,
                        :recipient_email,
                        :subject,
                        :idempotency_key,
                        'pending'
                    )
                    RETURNING *;
                """),
                dispatch_data
            )

            record = dict(result.mappings().one())
            session.commit()
            return record

        except IntegrityError as error:
            session.rollback()
            raise DuplicateDispatchError(
                "Dispatch already exists."
            ) from error

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def get_by_idempotency_key(self, idempotency_key: str):
        session = SessionLocal()

        try:
            result = session.execute(
                text("""
                    SELECT *
                    FROM dispatch_records
                    WHERE idempotency_key = :key;
                """),
                {"key": idempotency_key}
            )

            record = result.mappings().one_or_none()
            return dict(record) if record else None

        finally:
            session.close()

    def claim_dispatch(self, dispatch_id: str) -> dict:
        """Atomically claim a pending dispatch for sending."""

        session = SessionLocal()

        try:
            result = session.execute(
                text("""
                    UPDATE dispatch_records
                    SET
                        status = 'sending',
                        attempt_count = attempt_count + 1,
                        updated_at = NOW(),
                        last_error = NULL
                    WHERE dispatch_id = :dispatch_id
                      AND status = 'pending'
                    RETURNING *;
                """),
                {"dispatch_id": dispatch_id}
            )

            record = result.mappings().one_or_none()

            if record is None:
                raise DispatchStateError(
                    "Dispatch cannot be claimed. "
                    "It may already be processing or completed."
                )

            record = dict(record)
            session.commit()
            return record

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def update_status(
        self,
        dispatch_id: str,
        status: str,
        provider: str = None,
        provider_message_id: str = None,
        last_error: str = None
    ) -> dict:

        allowed_transitions = {
            "sent": ("sending",),
            "failed": ("sending",),
            "unknown": ("sending",),
        }

        if status not in allowed_transitions:
            raise ValueError(
                "Use claim_dispatch for sending or retry operations."
            )

        session = SessionLocal()

        try:
            result = session.execute(
                text("""
                    UPDATE dispatch_records
                    SET
                        status = :status,
                        provider = COALESCE(:provider, provider),
                        provider_message_id =
                            COALESCE(
                                :provider_message_id,
                                provider_message_id
                            ),
                        last_error = :last_error,
                        sent_at = CASE
                            WHEN :status = 'sent' THEN NOW()
                            ELSE sent_at
                        END,
                        updated_at = NOW()
                    WHERE dispatch_id = :dispatch_id
                      AND status = 'sending'
                    RETURNING *;
                """),
                {
                    "dispatch_id": dispatch_id,
                    "status": status,
                    "provider": provider,
                    "provider_message_id": provider_message_id,
                    "last_error": last_error
                }
            )

            record = result.mappings().one_or_none()

            if record is None:
                raise DispatchStateError(
                    "Invalid dispatch state transition."
                )

            record = dict(record)
            session.commit()
            return record

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def retry_failed_dispatch(self, dispatch_id: str) -> dict:
        """Allow only a confirmed failed dispatch to be retried."""

        session = SessionLocal()

        try:
            result = session.execute(
                text("""
                    UPDATE dispatch_records
                    SET
                        status = 'pending',
                        updated_at = NOW(),
                        last_error = NULL
                    WHERE dispatch_id = :dispatch_id
                      AND status = 'failed'
                    RETURNING *;
                """),
                {"dispatch_id": dispatch_id}
            )

            record = result.mappings().one_or_none()

            if record is None:
                raise DispatchStateError(
                    "Only failed dispatches can be retried."
                )

            record = dict(record)
            session.commit()
            return record

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def reconcile_dispatch(
        self,
        dispatch_id: str,
        final_status: str,
        provider_message_id: str = None,
        last_error: str = None
    ) -> dict:
        """Resolve an uncertain dispatch using provider evidence."""

        if final_status not in ("sent", "failed"):
            raise ValueError(
                "Reconciliation status must be sent or failed."
            )

        session = SessionLocal()

        try:
            result = session.execute(
                text("""
                    UPDATE dispatch_records
                    SET
                        status = :status,
                        provider_message_id = COALESCE(
                            :provider_message_id,
                            provider_message_id
                        ),
                        last_error = :last_error,
                        sent_at = CASE
                            WHEN :status = 'sent' THEN NOW()
                            ELSE sent_at
                        END,
                        updated_at = NOW()
                    WHERE dispatch_id = :dispatch_id
                      AND status = 'unknown'
                    RETURNING *;
                """),
                {
                    "dispatch_id": dispatch_id,
                    "status": final_status,
                    "provider_message_id": provider_message_id,
                    "last_error": last_error
                }
            )

            record = result.mappings().one_or_none()

            if record is None:
                raise DispatchStateError(
                    "Only unknown dispatches can be reconciled."
                )

            record = dict(record)
            session.commit()
            return record

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()
