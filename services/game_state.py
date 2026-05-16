"""
GameState - 게임의 전체 상태를 관리하는 싱글톤 클래스.

모든 시스템(인벤토리, 퍼즐, 조사, 이벤트 등)이 이 클래스를 통해
상태를 읽고 쓴다. 즉 "단일 진실의 원천(Single Source of Truth)" 역할.

[자료구조 사용]
- 딕셔너리: 전체 상태 직렬화 (to_dict)
- 리스트: inventory, found_clues, view_stack, event_queue
- 셋:     solved_puzzles, investigated_objects (중복 방지)

[모드]
- "first_person" : 1인칭 탐색 모드
- "maze"         : 미로 탈출 모드

[상태]
- "playing"  : 진행 중
- "cleared"  : 클리어
- "failed"   : 실패
"""


class GameState:
    """게임 전체 상태를 보관하는 싱글톤 클래스."""

    # 클래스 변수로 단일 인스턴스를 보관
    _instance = None

    def __new__(cls):
        # 싱글톤 패턴 - 처음 호출될 때만 객체를 만들고, 이후엔 같은 객체 반환
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # __init__은 매번 호출되므로, 이미 초기화됐다면 다시 하지 않음
        if self._initialized:
            return
        self._initialized = True
        self.init_state()

    # ------------------------------------------------------------------
    # 초기화 / 리셋
    # ------------------------------------------------------------------
    def init_state(self):
        """게임을 처음 시작하거나 재시작할 때 초기 상태로 설정."""
        # 게임 모드: "first_person" | "maze"
        self.mode = "first_person"

        # 현재 위치
        self.current_room = "main_lab"
        self.current_view = "center"   # left | center | right

        # 인벤토리 (리스트) - 보유 아이템 ID 목록
        self.inventory = []

        # 해결한 퍼즐 (셋) - 중복 방지
        self.solved_puzzles = set()

        # 조사 완료한 오브젝트 (셋) - 중복 방지
        self.investigated_objects = set()

        # 발견한 단서 (리스트) - 순서 보존
        self.found_clues = []

        # 화면 히스토리 (스택) - 뒤로가기용
        self.view_stack = []

        # 이벤트 큐 (큐) - 순차 처리할 알림/이벤트
        self.event_queue = []

        # AI 힌트 호출 횟수 (rate limit용)
        self.ai_query_count = 0

        # 게임 상태: "playing" | "cleared" | "failed"
        self.status = "playing"

    def reset(self):
        """게임을 처음 상태로 되돌린다."""
        self.init_state()

    # ------------------------------------------------------------------
    # 조회 / 갱신
    # ------------------------------------------------------------------
    def get_state(self) -> dict:
        """현재 상태를 딕셔너리로 반환 (JSON 응답용)."""
        return self.to_dict()

    def update_state(self, key: str, value) -> None:
        """상태 필드 하나를 갱신.

        예) update_state("current_view", "left")
        """
        if not hasattr(self, key):
            raise KeyError(f"GameState에 '{key}' 필드가 없습니다.")
        setattr(self, key, value)

    # ------------------------------------------------------------------
    # 모드 / 라이프사이클
    # ------------------------------------------------------------------
    def switch_mode(self, target_mode: str) -> None:
        """모드 전환 (first_person <-> maze)."""
        if target_mode not in ("first_person", "maze"):
            raise ValueError(f"알 수 없는 모드: {target_mode}")
        self.mode = target_mode

    def mark_cleared(self) -> None:
        """게임 클리어 처리."""
        self.status = "cleared"

    def mark_failed(self) -> None:
        """게임 실패 처리."""
        self.status = "failed"

    # ------------------------------------------------------------------
    # 직렬화
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """JSON 응답용 딕셔너리로 직렬화.

        주의: set 타입은 JSON으로 못 보내기 때문에 list로 변환한다.
        """
        return {
            "mode": self.mode,
            "current_room": self.current_room,
            "current_view": self.current_view,
            "inventory": self.inventory,
            "solved_puzzles": list(self.solved_puzzles),
            "investigated_objects": list(self.investigated_objects),
            "found_clues": self.found_clues,
            "view_stack": self.view_stack,
            "event_queue": self.event_queue,
            "ai_query_count": self.ai_query_count,
            "status": self.status,
        }


# 전역 싱글톤 인스턴스 (다른 모듈에서 `from services.game_state import game_state` 로 사용)
game_state = GameState()


# ----------------------------------------------------------------------
# 단독 실행시 동작 테스트
# ----------------------------------------------------------------------
if __name__ == "__main__":
    gs = GameState()
    print("[1] 초기 상태")
    print(gs.to_dict())

    print("\n[2] 인벤토리에 손전등 추가")
    gs.inventory.append("flashlight")
    print(gs.to_dict())

    print("\n[3] 시점을 왼쪽으로 변경")
    gs.update_state("current_view", "left")
    print(gs.to_dict())

    print("\n[4] 퍼즐 'cabinet_password' 해결")
    gs.solved_puzzles.add("cabinet_password")
    print(gs.to_dict())

    print("\n[5] 모드 전환 (미로)")
    gs.switch_mode("maze")
    print(gs.to_dict())

    print("\n[6] 리셋")
    gs.reset()
    print(gs.to_dict())

    print("\n[7] 싱글톤 확인 (gs == gs2)")
    gs2 = GameState()
    print(f"같은 객체인가? {gs is gs2}")
