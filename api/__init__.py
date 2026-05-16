"""
API 공통 모듈.

- 에러 코드 상수
- 성공/실패 응답 헬퍼

[응답 형식]
성공:
    {
        "success": true,
        "data": { ... },
        "state_changed": { ... },   (선택)
        "pending_events": [ ... ]   (선택)
    }

실패:
    {
        "success": false,
        "error_code": "WRONG_ANSWER",
        "message": "비밀번호가 일치하지 않습니다."
    }
"""
from flask import jsonify


# ----------------------------------------------------------------------
# 에러 코드 (API 명세서와 1:1 대응)
# ----------------------------------------------------------------------
class ErrorCode:
    INVALID_REQUEST      = "INVALID_REQUEST"       # 필수 파라미터 누락
    NOT_FOUND            = "NOT_FOUND"             # 존재하지 않는 ID
    INVALID_STATE        = "INVALID_STATE"         # 현재 상태에서 불가능
    ALREADY_DONE         = "ALREADY_DONE"          # 이미 처리됨
    MISSING_REQUIREMENT  = "MISSING_REQUIREMENT"   # 선행 조건 미충족
    WRONG_ANSWER         = "WRONG_ANSWER"          # 퍼즐 정답 오류
    COLLISION            = "COLLISION"             # 미로 벽 충돌
    INVALID_ITEM         = "INVALID_ITEM"          # 보유하지 않은 아이템
    INVALID_TARGET       = "INVALID_TARGET"        # 잘못된 사용 대상


# ----------------------------------------------------------------------
# 응답 빌더
# ----------------------------------------------------------------------
def success(
    data: dict | None = None,
    state_changed: dict | None = None,
    pending_events: list | None = None,
    status_code: int = 200,
):
    """성공 응답 생성.

    Args:
        data:           실제 응답 데이터 본체
        state_changed:  변경된 GameState 필드만 (프론트 동기화 최적화)
        pending_events: 이번 행동으로 발생한 이벤트 목록
        status_code:    HTTP 상태 코드 (기본 200)
    """
    body = {"success": True}
    if data is not None:
        body["data"] = data
    if state_changed is not None:
        body["state_changed"] = state_changed
    if pending_events is not None:
        body["pending_events"] = pending_events
    return jsonify(body), status_code


def error(
    error_code: str,
    message: str,
    status_code: int = 400,
):
    """실패 응답 생성.

    Args:
        error_code:  ErrorCode.* 중 하나
        message:     사용자에게 보여줄 한글 메시지
        status_code: HTTP 상태 코드 (기본 400)
    """
    body = {
        "success": False,
        "error_code": error_code,
        "message": message,
    }
    return jsonify(body), status_code
