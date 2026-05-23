"""
UI 보조 API.

- GET /api/ui/clues   : 단서창 (최신순) - 스택 자료구조 활용
- GET /api/ui/minimap : 미니맵 데이터 (모드에 따라 분기)
"""
from flask import Blueprint

from api import success, error, ErrorCode
from services.game_state import game_state
from services.room_graph import RoomGraph
from utils.data_loader import get_data


ui_bp = Blueprint("ui", __name__, url_prefix="/api/ui")


def _enrich_clue(clue_id: str) -> dict:
    """단서 ID에 표시용 텍스트를 붙여 반환 (프론트가 그대로 쓸 수 있도록)."""
    # 명시적 매핑이 있는 케이스
    explicit = {
        "clue_2": "숫자 '2'",
        "clue_3": "숫자 '3'",
        "clue_6": "숫자 '6'",
        "clue_9": "숫자 '9'",
        "birthday_0418": "생일 4월 18일 (0418)",
        "research_doc": "연구 일지 문서",
        "code_note": "코드 매핑 노트",
        "word_bang": "해독된 단어: BANG",
    }
    return {
        "id": clue_id,
        "display": explicit.get(clue_id, clue_id),
    }


@ui_bp.route("/clues", methods=["GET"])
def get_clues():
    """단서창 - 최신 발견순으로 정렬해서 반환."""
    clue_ids = game_state.found_clues.to_list_newest_first()
    return success(data={
        "clues": [_enrich_clue(cid) for cid in clue_ids],
        "count": len(clue_ids),
    })


@ui_bp.route("/minimap", methods=["GET"])
def get_minimap():
    """미니맵 데이터.

    - 1인칭: 방 그래프 + 현재 방
    - 미로:  미로 그리드 + 플레이어 위치 (함정은 숨김)
    """
    if game_state.mode == "first_person":
        rooms_data = get_data()["rooms"]
        graph = RoomGraph.from_rooms_data(rooms_data)
        return success(data={
            "mode": "first_person",
            "rooms": [
                {
                    "id": rid,
                    "name": info.get("name", rid),
                    "neighbors": graph.get_neighbors(rid),
                }
                for rid, info in rooms_data.items()
            ],
            "current_room": game_state.current_room,
            "current_view": game_state.current_view,
        })

    if game_state.mode == "maze":
        if not game_state.maze_grid:
            return error(ErrorCode.INVALID_STATE, "미로가 아직 생성되지 않았습니다.")
        return success(data={
            "mode": "maze",
            "grid": game_state.maze_grid,
            "current_position": list(game_state.maze_position),
            "exit": list(game_state.maze_exit),
            "dimensions": {
                "width": len(game_state.maze_grid[0]),
                "height": len(game_state.maze_grid),
            },
        })

    return error(ErrorCode.INVALID_STATE, f"알 수 없는 모드: {game_state.mode}")
