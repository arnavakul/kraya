
import json

from sqlalchemy import text

from pydantic_models.email_message import EmailMessage
from pydantic_models.inbox_triage_result import InboxTriageResult


class InboxRepository:

    def __init__(self, session_factory=None):
        self._session_factory = session_factory

    def _get_session_factory(self):
        if self._session_factory is None:
            from services.database import SessionLocal
            return SessionLocal

        return self._session_factory

    def claim_email(self, email: EmailMessage) -> bool:
        """
        Atomically register and claim a new email.

        Returns True if this worker claimed it.
        Returns False if the email already exists.
        """

        session_factory = self._get_session_factory()

        query = text("""
            INSERT INTO inbox_emails (
                email_id,
                sender_email,
                sender_name,
                subject,
                thread_id,
                received_at,
                processing_status
            )
            VALUES (
                :email_id,
                :sender_email,
                :sender_name,
                :subject,
                :thread_id,
                :received_at,
                'processing'
            )
            ON CONFLICT (email_id) DO NOTHING
            RETURNING email_id
        """)

        with session_factory() as session:
            with session.begin():

                result = session.execute(
                    query,
                    {
                        "email_id": email.email_id,
                        "sender_email": email.sender_email,
                        "sender_name": email.sender_name,
                        "subject": email.subject,
                        "thread_id": email.thread_id,
                        "received_at": email.received_at,
                    }
                )

                return result.scalar_one_or_none() is not None

    def complete_email(
        self,
        email_id: str,
        result: InboxTriageResult
    ) -> bool:
        """
        Save triage results and mark the email completed.
        Only a currently processing email can be completed.
        """

        if result.email_id != email_id:
            raise ValueError("Email IDs do not match.")

        session_factory = self._get_session_factory()

        query = text("""
            UPDATE inbox_emails
            SET
                category = :category,
                confidence = :confidence,
                summary = :summary,
                routing_action = :routing_action,
                requires_human_review = :requires_human_review,
                security_flags = CAST(:security_flags AS JSONB),
                processing_status = 'completed',
                last_error = NULL,
                processed_at = NOW(),
                updated_at = NOW()
            WHERE email_id = :email_id
              AND processing_status = 'processing'
            RETURNING email_id
        """)

        with session_factory() as session:
            with session.begin():

                result = session.execute(
                    query,
                    {
                        "email_id": email_id,
                        "category": result.category,
                        "confidence": result.confidence,
                        "summary": result.summary,
                        "routing_action": result.routing_action,
                        "requires_human_review": result.requires_human_review,
                        "security_flags": json.dumps(result.security_flags),
                    }
                )

                return result.scalar_one_or_none() is not None

    def fail_email(
        self,
        email_id: str,
        error_message: str
    ) -> bool:
        """
        Mark a currently processing email as failed.
        """

        session_factory = self._get_session_factory()

        query = text("""
            UPDATE inbox_emails
            SET
                processing_status = 'failed',
                last_error = :error_message,
                updated_at = NOW()
            WHERE email_id = :email_id
              AND processing_status = 'processing'
            RETURNING email_id
        """)

        with session_factory() as session:
            with session.begin():

                result = session.execute(
                    query,
                    {
                        "email_id": email_id,
                        "error_message": error_message[:2000],
                    }
                )

                return result.scalar_one_or_none() is not None

    def retry_failed_email(self, email_id: str) -> bool:
        """
        Explicitly move a failed email back to processing.

        Completed or currently processing emails cannot be retried.
        """

        session_factory = self._get_session_factory()

        query = text("""
            UPDATE inbox_emails
            SET
                processing_status = 'processing',
                last_error = NULL,
                updated_at = NOW()
            WHERE email_id = :email_id
              AND processing_status = 'failed'
            RETURNING email_id
        """)

        with session_factory() as session:
            with session.begin():

                result = session.execute(
                    query,
                    {"email_id": email_id}
                )

                return result.scalar_one_or_none() is not None
