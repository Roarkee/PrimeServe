
import logging
import os
import socket
import time
from uuid import uuid4

import httpx
from sqlmodel import Session

from .database import engine
from .services.outbox_service import OutboxService


logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 2
BATCH_SIZE = 20
LEASE_SECONDS = 60
HTTP_TIMEOUT_SECONDS = 20

KITCHEN_INTERNAL_URL = os.getenv("KITCHEN_INTERNAL_URL")

if not KITCHEN_INTERNAL_URL:
    raise RuntimeError("KITCHEN_INTERNAL_URL is not configured")


def create_worker_id() -> str:
    return f"{socket.gethostname()}-{os.getpid()}-{uuid4().hex[:8]}"


def claim_events(worker_id: str):
    """Claim events in a short, independent database transaction."""
    with Session(engine) as session:
        return OutboxService.claim_pending_events(
            session,
            worker_id=worker_id,
            batch_size=BATCH_SIZE,
            lease_seconds=LEASE_SECONDS,
        )


def deliver_event(client: httpx.Client, event) -> None:
    """Deliver one event to Kitchen."""
    response = client.post(
        KITCHEN_INTERNAL_URL,
        json={
            "id": str(event.id),
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": str(event.aggregate_id),
            "aggregate_version": event.aggregate_version,
            "payload": event.payload,
        },
        headers={
            "Idempotency-Key": str(event.id),
        },
    )

    response.raise_for_status()


def acknowledge_published(event_id, worker_id: str) -> bool:
    with Session(engine) as session:
        try:
            published = OutboxService.mark_published(
                session,
                event_id=event_id,
                worker_id=worker_id,
            )

            session.commit()
            return published

        except Exception:
            session.rollback()
            raise


def acknowledge_failed(event, worker_id: str, error: str) -> bool:
    with Session(engine) as session:
        try:
            failed = OutboxService.mark_failed(
                session,
                event_id=event.id,
                worker_id=worker_id,
                attempts=event.attempts,
                error=error,
            )

            session.commit()
            return failed

        except Exception:
            session.rollback()
            raise


def process_event(client: httpx.Client, event, worker_id: str) -> None:
    try:
        deliver_event(client, event)

    except httpx.HTTPStatusError as exc:
        error = (
            f"Kitchen returned HTTP {exc.response.status_code}: "
            f"{exc.response.text[:1000]}"
        )

        logger.warning(
            "Delivery failed for event %s: %s",
            event.id,
            error,
        )

        acknowledge_failed(event, worker_id, error)

    except httpx.RequestError as exc:
        error = f"Kitchen request failed: {str(exc)[:1000]}"

        logger.warning(
            "Delivery failed for event %s: %s",
            event.id,
            error,
        )

        acknowledge_failed(event, worker_id, error)

    else:
        published = acknowledge_published(event.id, worker_id)

        if published:
            logger.info("Published outbox event %s", event.id)
        else:
            logger.warning(
                "Could not acknowledge event %s; worker lease may have expired",
                event.id,
            )


def run_worker() -> None:
    worker_id = create_worker_id()

    logger.info("Starting outbox worker: %s", worker_id)

    with httpx.Client(
        timeout=HTTP_TIMEOUT_SECONDS,
    ) as client:

        while True:
            try:
                events = claim_events(worker_id)

                if not events:
                    time.sleep(POLL_INTERVAL_SECONDS)
                    continue

                for event in events:
                    process_event(client, event, worker_id)

            except Exception:
                logger.exception("Outbox worker encountered an error")
                time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    run_worker()
