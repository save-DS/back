"""
이벤트 폴링 API.

- GET /api/events/pending : 이벤트 큐 조회
    * mode=peek (기본)  : 큐 내용만 확인 (소비 X)
    * mode=consume      : 큐에서 모두 꺼내며 반환 (큐가 비워짐)

[큐 자료구조]
event_queue (FIFO) — 시간 기반 알림, 경고 메시지 등이 enqueue되고
프론트가 주기적으로 폴링하여 dequeue 처리.
"""
from flask import Blueprint, request

from api import success
from services.game_state import game_state


events_bp = Blueprint("events", __name__, url_prefix="/api/events")


@events_bp.route("/pending", methods=["GET"])
def get_pending():
    mode = request.args.get("mode", "peek")

    if mode == "consume":
        consumed = []
        while not game_state.event_queue.is_empty():
            consumed.append(game_state.event_queue.dequeue())
        return success(
            data={"events": consumed, "consumed": True},
            state_changed={"event_queue": []},
        )

    # 기본: peek
    return success(data={
        "events": game_state.event_queue.to_list(),
        "consumed": False,
    })
