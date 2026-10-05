from datetime import date
from sqlalchemy import text
from sqlmodel import Session
from uuid import UUID


def generate_order_number(
    session: Session,
    restaurant_id: UUID,
    counter_date: date,
) -> int:

    result = session.exec(
        text("""
            INSERT INTO prime_orders.order_number_counters
                (id, restaurant_id, counter_date, last_number)
            VALUES
                (gen_random_uuid(), :restaurant_id, :counter_date, 1)

            ON CONFLICT (restaurant_id, counter_date)
            DO UPDATE SET
                last_number =
                    prime_orders.order_number_counters.last_number + 1

            RETURNING last_number
        """),
        params={
            "restaurant_id": str(restaurant_id),
            "counter_date": counter_date,
        },
    )

    return result.one()[0]