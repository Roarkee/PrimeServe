from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from sqlmodel import select
from ..models import PrepStation
from ..services.websocket_manager import websocket_manager
from ..database import SessionDep
from ..dependencies import verify_decode_token


router = APIRouter()


@router.websocket("/ws/kds/{station_id}")
async def kds_connection(websocket: WebSocket,station_id: UUID,session: SessionDep):
    await websocket.accept()

    registered = False

    try:
        auth_message = await websocket.receive_json()

        token = auth_message.get("token")

        if not isinstance(token, str) or not token:
            await websocket.close(code=1008, reason="Authentication required")
            return

        payload = verify_decode_token(token)

        if "kitchen:view" not in payload.get("permissions", []):
            await websocket.close(code=1008, reason="Permission denied")
            return

        restaurant_id = UUID(payload["restaurant_id"])


        station = session.exec(
            select(PrepStation).where(
                PrepStation.id == station_id,
                PrepStation.restaurant_id == restaurant_id,
                PrepStation.is_active.is_(True),
            )
        ).first()

        if station is None:
            await websocket.close(
                code=1008,
                reason="Invalid or inactive prep station",
            )
            return


        await websocket_manager.connect(
            websocket=websocket,
            restaurant_id=str(restaurant_id),
            branch_id=(
                str(station.branch_id)
                if station.branch_id is not None
                else None
            ),
            station_id=str(station.id),
        )

        registered = True

        await websocket.send_json({
            "event": "connection.ready",
            "data": {
                "restaurant_id": str(restaurant_id),
                "branch_id": (
                    str(station.branch_id)
                    if station.branch_id is not None
                    else None
                ),
                "station_id": str(station.id),
            },
        })


        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass

    except HTTPException:
        await websocket.close(
            code=1008,
            reason="Invalid authentication",
        )

    except (ValueError, KeyError, TypeError):
        await websocket.close(
            code=1008,
            reason="Invalid authentication data",
        )

    finally:
        if registered:
            websocket_manager.disconnect(websocket)