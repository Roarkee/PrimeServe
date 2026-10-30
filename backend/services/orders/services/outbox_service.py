
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy.orm import aliased
from sqlmodel import Session, select,update,and_,or_
from ..models import OutboxEvent


class OutboxService:
    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"

    MAX_ATTEMPTS = 10
    BASE_RETRY_SECONDS = 5
    MAX_RETRY_SECONDS = 900
    DEFAULT_BATCH_SIZE = 50
    DEFAULT_LEASE_SECONDS = 60

    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @classmethod
    def create_event(
        cls,
        session: Session,
        *,
        aggregate_type: str,
        aggregate_id: UUID,
        event_type: str,
        payload: dict,
        aggregate_version: int | None = None,
    ) -> OutboxEvent:
        event = OutboxEvent(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            aggregate_version=aggregate_version,
            payload=payload,
            status=cls.PENDING,
        )

        session.add(event)
        session.flush()

        return event

    @classmethod
    def claim_pending_events(
        cls,
        session: Session,
        *,
        worker_id: str,
        batch_size: int = DEFAULT_BATCH_SIZE,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> list[OutboxEvent]:
        """
        Atomically claim available events.

        This method owns its transaction and commits the claims.
        Use a dedicated session for this operation.
        """
        if not worker_id or len(worker_id) > 100:
            raise ValueError("worker_id must contain 1-100 characters")

        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero")

        if lease_seconds < 1:
            raise ValueError("lease_seconds must be greater than zero")

        now = cls.utc_now()
        lease_expiry = now + timedelta(seconds=lease_seconds)

        earlier_event = aliased(OutboxEvent)

        earlier_unpublished_exists = (
            select(1)
            .select_from(earlier_event)
            .where(
                earlier_event.aggregate_type == OutboxEvent.aggregate_type,
                earlier_event.aggregate_id == OutboxEvent.aggregate_id,
                earlier_event.aggregate_version < OutboxEvent.aggregate_version,
                earlier_event.status != cls.PUBLISHED,
            )
            .correlate(OutboxEvent)
            .exists()
        )

        statement = (
            select(OutboxEvent)
            .where(
                or_(
                    and_(
                        OutboxEvent.status == cls.PENDING,
                        OutboxEvent.available_at <= now,
                    ),
                    and_(
                        OutboxEvent.status == cls.PROCESSING,
                        OutboxEvent.locked_until <= now,
                    ),
                ),
                ~earlier_unpublished_exists,
            )
            .order_by(OutboxEvent.created_at, OutboxEvent.id)
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )

        try:
            events = list(session.exec(statement).all())

            for event in events:
                event.status = cls.PROCESSING
                event.locked_by = worker_id
                event.locked_until = lease_expiry
                event.attempts += 1

            session.commit()

            for event in events:
                session.refresh(event)

            return events

        except Exception:
            session.rollback()
            raise


    @classmethod
    def mark_published(
        cls,
        session: Session,
        *,
        event_id: UUID,
        worker_id: str,
    ) -> bool:
        statement = (
            update(OutboxEvent)
            .where(
                OutboxEvent.id == event_id,
                OutboxEvent.status == cls.PROCESSING,
                OutboxEvent.locked_by == worker_id,
            )
            .values(
                status=cls.PUBLISHED,
                published_at=cls.utc_now(),
                locked_by=None,
                locked_until=None,
                last_error=None,
            )
        )

        result = session.exec(statement)
        return result.rowcount == 1



    @classmethod
    def mark_failed(
        cls,
        session: Session,
        *,
        event_id: UUID,
        worker_id: str,
        error: str,
    ) -> bool:
        event = session.get(OutboxEvent, event_id)

        if (
            event is None
            or event.status != cls.PROCESSING
            or event.locked_by != worker_id
        ):
            return False

        now = cls.utc_now()
        
        if event.attempts < 1:
            raise ValueError("attempts must be at least 1")

        if event.attempts >= cls.MAX_ATTEMPTS:
            new_status = cls.FAILED
            available_at = event.available_at
        else:
            delay = min(
                cls.BASE_RETRY_SECONDS * (2 ** (event.attempts - 1)),
                cls.MAX_RETRY_SECONDS,
            )
            new_status = cls.PENDING
            available_at = now + timedelta(seconds=delay)

        statement = (
            update(OutboxEvent)
            .where(
                OutboxEvent.id == event_id,
                OutboxEvent.status == cls.PROCESSING,
                OutboxEvent.locked_by == worker_id,
            )
            .values(
                status=new_status,
                available_at=available_at,
                locked_by=None,
                locked_until=None,
                last_error=error[:4000],
            )
        )

        result = session.exec(statement)
        return result.rowcount == 1
