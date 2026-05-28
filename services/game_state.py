"""
GameState - 게임의 전체 상태를 관리하는 싱글톤 클래스.

모든 시스템(인벤토리, 퍼즐, 조사, 이벤트 등)이 이 클래스를 통해
상태를 읽고 쓴다. 즉 "단일 진실의 원천(Single Source of Truth)" 역할.

[자료구조 모듈 사용]
- Inventory : 인벤토리 (리스트 + 셋)
- Stack     : found_clues, view_stack (스택)
- Queue     : event_queue (큐)
- set       : solved_puzzles, investigated_objects (파이썬 내장 셋)

[모드]
- "first_person" : 1인칭 탐색 모드
- "maze"         : 미로 탈출 모드

[상태]
- "playing"  : 진행 중
- "cleared"  : 클리어
- "failed"   : 실패
"""
from services.inventory import Inventory
from services.clue_stack import Stack
from services.event_queue import Queue


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

        # 인벤토리 (리스트 + 셋)
        self.inventory = Inventory(max_size=8)

        # 해결한 퍼즐 / 조사한 오브젝트 (셋 - 중복 방지)
        self.solved_puzzles: set[str] = set()
        self.investigated_objects: set[str] = set()
        # 어느 오브젝트에서 아이템을 꺼냈는지 (셋)
        # 예: 캐비닛에서 건전지 꺼냄 → 'cabinet' 추가 → 다음 조사 시 shelf2 표시
        self.taken_from_objects: set[str] = set()

        # 발견한 단서 (스택 - 최신순 표시용)
        self.found_clues = Stack()

        # 화면 히스토리 (스택 - 뒤로가기용)
        self.view_stack = Stack()

        # 이벤트 큐 (큐 - 순차 처리)
        self.event_queue = Queue()

        # AI 힌트 호출 횟수 (rate limit용)
        self.ai_query_count = 0

        # ----- 미로 모드 관련 -----
        self.maze_grid: list[list[int]] = []
        self.maze_start: tuple[int, int] | None = None
        self.maze_exit: tuple[int, int] | None = None
        # 함정 좌표는 백엔드만 알고 있음. to_dict()에서 제외 (보안)
        self.maze_traps: set[tuple[int, int]] = set()
        self.maze_position: tuple[int, int] | None = None
        self.maze_steps = 0
        self.maze_trap_hits = 0
        self.maze_reached_exit = False

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

        커스텀 클래스(Inventory/Stack/Queue)와 set은 모두
        JSON 호환 형태(list)로 변환한다.
        주의: maze_traps는 보안상 응답에서 제외 (함정은 플레이어에게 숨김).
        """
        return {
            "mode": self.mode,
            "current_room": self.current_room,
            "current_view": self.current_view,
            "inventory": self.inventory.to_list(),
            "solved_puzzles": list(self.solved_puzzles),
            "investigated_objects": list(self.investigated_objects),
            "taken_from_objects": list(self.taken_from_objects),
            "found_clues": self.found_clues.to_list_newest_first(),
            "view_stack": self.view_stack.to_list(),
            "event_queue": self.event_queue.to_list(),
            "ai_query_count": self.ai_query_count,
            # 미로 관련 (traps는 제외)
            "maze_grid": self.maze_grid,
            "maze_start": list(self.maze_start) if self.maze_start else None,
            "maze_exit": list(self.maze_exit) if self.maze_exit else None,
            "maze_position": list(self.maze_position) if self.maze_position else None,
            "maze_steps": self.maze_steps,
            "maze_trap_hits": self.maze_trap_hits,
            "maze_reached_exit": self.maze_reached_exit,
            "status": self.status,
        }


# 전역 싱글톤 인스턴스 (다른 모듈에서 `from services.game_state import game_state` 로 사용)
game_state = GameState()


# ----------------------------------------------------------------------
# 단독 실행 테스트
# ----------------------------------------------------------------------
if __name__ == "__main__":
    gs = GameState()
    print("[1] 초기 상태")
    print(gs.to_dict())

    print("\n[2] 인벤토리에 손전등/건전지 추가 (Inventory 클래스)")
    gs.inventory.add("flashlight")
    gs.inventory.add("battery")
    print(gs.to_dict()["inventory"])

    print("\n[3] 시점을 왼쪽으로 변경, 직전 화면 스택에 push")
    gs.view_stack.push("main_view:center")
    gs.update_state("current_view", "left")
    print("current_view:", gs.current_view)
    print("view_stack:", gs.view_stack.to_list())

    print("\n[4] 퍼즐 'cabinet_password' 해결 (set)")
    gs.solved_puzzles.add("cabinet_password")
    print("solved_puzzles:", gs.to_dict()["solved_puzzles"])

    print("\n[5] 단서 3개 발견 (Stack - 최신순)")
    gs.found_clues.push("clue_3")
    gs.found_clues.push("clue_9")
    gs.found_clues.push("clue_6")
    print("found_clues (최신순):", gs.to_dict()["found_clues"])

    print("\n[6] 이벤트 큐에 알림 enqueue (Queue)")
    gs.event_queue.enqueue({"type": "warning", "text": "정전 임박!"})
    gs.event_queue.enqueue({"type": "narration", "text": "전기가 꺼졌다"})
    print("event_queue:", gs.to_dict()["event_queue"])

    print("\n[7] 모드 전환 (미로)")
    gs.switch_mode("maze")
    print("mode:", gs.mode)

    print("\n[8] 리셋")
    gs.reset()
    print(gs.to_dict())

    print("\n[9] 싱글톤 확인")
    gs2 = GameState()
    print(f"같은 객체인가? {gs is gs2}")
