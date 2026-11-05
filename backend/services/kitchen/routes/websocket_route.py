import asyncio
import logging
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from sqlmodel import select

from ..models import PrepStation
from ..services.websocket_manager import websocket_manager
from ..database import SessionDep
from ..utils import verify_decode_token

logger = logging.getLogger(__name__)

router = APIRouter()

AUTH_TIMEOUT_SECONDS = 5.0


async def _safe_close(websocket: WebSocket, code: int = 1008, reason: str = "") -> None:
    """Safely close a websocket without raising unhandled ASGI state errors."""
    try:
        await websocket.close(code=code, reason=reason[:120])
    except Exception:
        pass


@router.websocket("/ws/kds/{station_id}")
async def kds_connection(
    websocket: WebSocket,
    station_id: UUID,
    session: SessionDep,
):
    await websocket.accept()

    registered = False

    try:
        # Enforce an authentication timeout to prevent unauthenticated connections hanging indefinitely.
        try:
            auth_message = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=AUTH_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            await _safe_close(websocket, code=1008, reason="Authentication timeout")
            return

        if not isinstance(auth_message, dict):
            await _safe_close(websocket, code=1008, reason="Invalid authentication message format")
            return

        token = auth_message.get("token")
        if not isinstance(token, str) or not token:
            await _safe_close(websocket, code=1008, reason="Authentication required")
            return

        # Decode and validate token using existing JWT utility.
        try:
            payload = verify_decode_token(token)
        except HTTPException as exc:
            await _safe_close(websocket, code=1008, reason=exc.detail)
            return

        # Permission check: kitchen:view is required for KDS connection.
        permissions = payload.get("permissions", [])
        if "kitchen:view" not in permissions:
            await _safe_close(websocket, code=1008, reason="Permission denied")
            return

        # Restaurant tenant isolation: extract restaurant_id from trusted JWT payload.
        token_restaurant_id = payload.get("restaurant_id")
        if not token_restaurant_id:
            await _safe_close(websocket, code=1008, reason="Missing restaurant_id in token")
            return

        try:
            restaurant_id = UUID(str(token_restaurant_id))
        except (ValueError, TypeError):
            await _safe_close(websocket, code=1008, reason="Invalid restaurant_id in token")
            return

        # Verify the requested prep station belongs to the authenticated restaurant and is active.
        station = session.exec(
            select(PrepStation).where(
                PrepStation.id == station_id,
                PrepStation.restaurant_id == restaurant_id,
                PrepStation.is_active.is_(True),
            )
        ).first()

        if station is None:
            await _safe_close(websocket, code=1008, reason="Invalid or inactive prep station")
            return

        # Register connection in WebSocket manager.
        websocket_manager.connect(
            websocket=websocket,
            restaurant_id=str(restaurant_id),
            station_id=str(station.id),
        )
        registered = True

        # Send connection.ready confirmation to KDS client.
        await websocket.send_json({
            "event": "connection.ready",
            "data": {
                "restaurant_id": str(restaurant_id),
                "station_id": str(station.id),
                "station_name": station.name,
            },
        })

        # Keep connection open and listen for client messages / pings.
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        logger.debug("KDS client disconnected: station=%s", station_id)

    except Exception as exc:
        logger.warning("Unexpected error in KDS websocket for station %s: %s", station_id, exc)
        await _safe_close(websocket, code=1011, reason="Internal server error")

    finally:
        if registered:
            websocket_manager.disconnect(websocket)
