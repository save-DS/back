"""
게임 라이프사이클 API.

- POST /api/game/init   : 게임 초기화 + 인트로 반환
- GET  /api/game/state  : 현재 GameState 전체 반환
- POST /api/game/reset  : 처음부터 다시 시작
"""
from flask import Blueprint

from api import success
from services.game_state import game_state


game_bp = Blueprint("game", __name__, url_prefix="/api/game")


INTRO_EVENT = {
    "type": "intro",
    "narration": (
        "정신을 차려보니 낯선 폐연구실에 갇혀있다. "
        "주변을 둘러보며 탈출할 방법을 찾아야 한다."
    ),
}


@game_bp.route("/init", methods=["POST"])
def init_game():
    """게임 처음 시작: 상태 초기화 + 인트로 이벤트."""
    game_state.reset()
    return success(data={
        "state": game_state.to_dict(),
        "intro_event": INTRO_EVENT,
    })


@game_bp.route("/state", methods=["GET"])
def get_state():
    """현재 게임 상태 조회."""
    return success(data={"state": game_state.to_dict()})


@game_bp.route("/reset", methods=["POST"])
def reset_game():
    """게임 재시작 (init과 동일 동작)."""
    game_state.reset()
    return success(data={
        "state": game_state.to_dict(),
        "intro_event": INTRO_EVENT,
    })
