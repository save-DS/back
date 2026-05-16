"""
Stack - LIFO(Last In First Out) 자료구조.

[게임 내 사용처]
- found_clues : 최근 발견한 단서를 위에 쌓고, 최신순으로 보여주기
- view_stack  : 상세 뷰에서 ← 버튼 누르면 직전 화면으로 복귀

[구현 메모]
- 파이썬 list의 append/pop을 사용하면 양 끝 연산이 O(1)이라 스택에 적합
- 파일명을 clue_stack.py로 한 이유: 주된 용도가 단서 관리이기 때문
  하지만 클래스 자체는 범용 Stack이라 view_stack 등에도 재사용
"""


class Stack:
    """범용 LIFO 스택."""

    def __init__(self):
        # list의 끝(append/pop)을 스택의 top으로 사용
        self._items: list = []

    # ------------------------------------------------------------------
    # 핵심 연산
    # ------------------------------------------------------------------
    def push(self, item) -> None:
        """스택 맨 위에 추가."""
        self._items.append(item)

    def pop(self):
        """맨 위 아이템 꺼내기. 비어있으면 None 반환."""
        if self.is_empty():
            return None
        return self._items.pop()

    def peek(self):
        """맨 위 아이템 확인만 (꺼내지 않음). 비어있으면 None."""
        if self.is_empty():
            return None
        return self._items[-1]

    # ------------------------------------------------------------------
    # 상태 조회
    # ------------------------------------------------------------------
    def is_empty(self) -> bool:
        return len(self._items) == 0

    def size(self) -> int:
        return len(self._items)

    # ------------------------------------------------------------------
    # 기타
    # ------------------------------------------------------------------
    def clear(self) -> None:
        self._items.clear()

    def to_list(self) -> list:
        """JSON 직렬화용. 바닥(처음 추가)부터 top(최근 추가) 순서로 반환."""
        return list(self._items)

    def to_list_newest_first(self) -> list:
        """최신 추가 순서대로 반환 (UI에 단서를 최신순 표시할 때 사용)."""
        return list(reversed(self._items))

    def __repr__(self) -> str:
        return f"Stack({self._items})"


# ----------------------------------------------------------------------
# 단독 실행 테스트
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("===== 시나리오 1: 단서 스택 =====")
    clues = Stack()
    clues.push("clue_3")
    clues.push("clue_9")
    clues.push("clue_6")
    print("발견 순서대로:", clues.to_list())                # [clue_3, clue_9, clue_6]
    print("최신순 표시:",   clues.to_list_newest_first())   # [clue_6, clue_9, clue_3]
    print("맨 위 확인:",    clues.peek())                   # clue_6
    print("크기:",          clues.size())                   # 3

    print("\n===== 시나리오 2: 화면 히스토리 =====")
    view = Stack()
    view.push("main_view:center")
    view.push("detail:cabinet")
    view.push("modal:password_input")
    print("현재 깊이:", view.size())
    print("뒤로가기 1:", view.pop())   # modal:password_input
    print("뒤로가기 2:", view.pop())   # detail:cabinet
    print("남은 거:",   view.peek())  # main_view:center

    print("\n===== 비어있을 때 안전성 =====")
    empty = Stack()
    print("pop:", empty.pop())     # None
    print("peek:", empty.peek())   # None
    print("is_empty:", empty.is_empty())   # True
