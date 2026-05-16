"""
방 이동 API.

- POST /api/move/room : 인접한 방으로 이동 (1인칭 모드)

[그래프 활용]
RoomGraph로 현재 방과 target_room이 연결되었는지 확인.
연결되지 않은 방은 MISSING_REQUIREMENT 에러.
"""
from flask import Blueprint, request

from api import success, error, ErrorCode
from services.game_state import game_state
from services.room_graph import RoomGraph
from utils.data_loader import get_data


move_bp = Blueprint("move", __name__, url_prefix="/api/move")


def _get_room_graph() -> RoomGraph:
    """rooms.json 데이터로 RoomGraph 생성 (요청마다 만들어도 가벼움)."""
    return RoomGraph.from_rooms_data(get_data()["rooms"])


@move_bp.route("/room", methods=["POST"])
def move_room():
    body = request.get_json(silent=True) or {}
    target_room_id = body.get("target_room_id")

    if not target_room_id:
        return error(ErrorCode.INVALID_REQUEST, "target_room_id가 필요합니다.")

    if game_state.mode != "first_person":
        return error(
            ErrorCode.INVALID_STATE,
            "1인칭 모드에서만 방 이동이 가능합니다.",
        )

    rooms = get_data()["rooms"]
    if target_room_id not in rooms:
        return error(ErrorCode.NOT_FOUND, f"'{target_room_id}' 방이 없습니다.")

    if target_room_id == game_state.current_room:
        return error(ErrorCode.INVALID_STATE, "이미 그 방에 있습니다.")

    graph = _get_room_graph()
    if not graph.is_connected(game_state.current_room, target_room_id):
        return error(
            ErrorCode.MISSING_REQUIREMENT,
            f"'{target_room_id}' 방은 현재 위치에서 직접 갈 수 없습니다.",
        )

    # 이동 처리
    game_state.current_room = target_room_id
    game_state.current_view = "center"   # 새 방은 항상 중앙 시점에서 시작

    return success(
        data={
            "current_room": target_room_id,
            "room_info": rooms[target_room_id],
        },
        state_changed={
            "current_room": target_room_id,
            "current_view": "center",
        },
    )
