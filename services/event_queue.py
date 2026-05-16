"""
Queue - FIFO(First In First Out) 자료구조.

[게임 내 사용처]
- event_queue       : 시간 기반 이벤트, 알림, 대화 순서 처리
- 정전/경보 연출 순서 등

[구현 메모]
- 파이썬 list로 큐를 만들면 dequeue가 O(n)이라 느림 (앞쪽 요소 제거시 전체 shift)
- collections.deque를 쓰면 양쪽 끝 연산이 모두 O(1)
"""
from collections import deque


class Queue:
    """범용 FIFO 큐 (deque 기반)."""

    def __init__(self):
        self._items: deque = deque()

    # ------------------------------------------------------------------
    # 핵심 연산
    # ------------------------------------------------------------------
    def enqueue(self, item) -> None:
        """뒤쪽에 추가."""
        self._items.append(item)

    def dequeue(self):
        """앞쪽에서 꺼내기. 비어있으면 None."""
        if self.is_empty():
            return None
        return self._items.popleft()

    def peek(self):
        """가장 앞 아이템 확인 (꺼내지 않음)."""
        if self.is_empty():
            return None
        return self._items[0]

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
        """JSON 직렬화용. 앞(가장 먼저 들어온 것)부터 반환."""
        return list(self._items)

    def __repr__(self) -> str:
        return f"Queue({list(self._items)})"


# ----------------------------------------------------------------------
# 단독 실행 테스트
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("===== 시나리오: 이벤트 큐 =====")
    events = Queue()

    # 게임 중 이벤트가 순차적으로 발생
    events.enqueue({"type": "narration", "text": "방에 들어왔다..."})
    events.enqueue({"type": "warning",   "text": "정전이 발생할지도 모른다"})
    events.enqueue({"type": "item",      "text": "건전지를 획득했다"})

    print(f"대기중 이벤트: {events.size()}개")
    print(f"맨 앞:        {events.peek()}")

    print("\n순차 처리:")
    while not events.is_empty():
        evt = events.dequeue()
        print(f"  처리: {evt}")

    print(f"\n처리 후 큐:    {events}")
    print(f"is_empty?:     {events.is_empty()}")
