"""
Inventory - 플레이어의 인벤토리 관리 클래스.

[자료구조]
- 리스트(_items)  : 획득 순서 보존
- 셋(_lookup)     : 보유 여부를 O(1)로 빠르게 조회 (중복 획득 방지)

리스트만 쓰면 has() 검사가 O(n)이라 느려지고, 셋만 쓰면 순서가 사라진다.
두 자료구조를 같이 써서 양쪽의 장점을 얻는 패턴.
"""


class Inventory:
    """리스트+셋 기반 인벤토리."""

    def __init__(self, max_size: int = 8):
        """
        Args:
            max_size: 슬롯 개수 (와이어프레임의 하단 인벤토리 바 기준)
        """
        self._items: list[str] = []      # 획득 순서대로 아이템 ID 저장
        self._lookup: set[str] = set()    # 빠른 검색용 (중복 방지)
        self.max_size = max_size

    # ------------------------------------------------------------------
    # 핵심 동작
    # ------------------------------------------------------------------
    def add(self, item_id: str) -> bool:
        """아이템을 추가. 이미 보유했거나 가득 차있으면 False 반환.

        Returns:
            True  : 새로 추가됨
            False : 이미 보유 중이거나 슬롯이 가득 참
        """
        if item_id in self._lookup:
            return False
        if self.is_full():
            return False
        self._items.append(item_id)
        self._lookup.add(item_id)
        return True

    def remove(self, item_id: str) -> bool:
        """아이템 제거 (사용/조합 등으로 소모될 때).

        Returns:
            True  : 제거 성공
            False : 보유하지 않은 아이템
        """
        if item_id not in self._lookup:
            return False
        self._items.remove(item_id)
        self._lookup.discard(item_id)
        return True

    def has(self, item_id: str) -> bool:
        """보유 여부 확인 (O(1) - 셋 활용)."""
        return item_id in self._lookup

    # ------------------------------------------------------------------
    # 조회
    # ------------------------------------------------------------------
    def get_all(self) -> list[str]:
        """획득 순서대로 아이템 목록 반환 (사본)."""
        return list(self._items)

    def count(self) -> int:
        """현재 보유 아이템 수."""
        return len(self._items)

    def is_full(self) -> bool:
        """슬롯이 가득 찼는지."""
        return len(self._items) >= self.max_size

    def is_empty(self) -> bool:
        return len(self._items) == 0

    # ------------------------------------------------------------------
    # 기타
    # ------------------------------------------------------------------
    def clear(self) -> None:
        """전체 비우기."""
        self._items.clear()
        self._lookup.clear()

    def to_list(self) -> list[str]:
        """JSON 직렬화용."""
        return self.get_all()

    def __repr__(self) -> str:
        return f"Inventory({self._items}, {self.count()}/{self.max_size})"


# ----------------------------------------------------------------------
# 단독 실행 테스트
# ----------------------------------------------------------------------
if __name__ == "__main__":
    inv = Inventory(max_size=4)
    print("[1] 빈 인벤토리:", inv)

    print("\n[2] 아이템 추가")
    print("  battery 추가:", inv.add("battery"))         # True
    print("  flashlight 추가:", inv.add("flashlight"))   # True
    print("  battery 또 추가:", inv.add("battery"))      # False (중복)
    print("  현재:", inv)

    print("\n[3] 보유 검사 (O(1) 셋 활용)")
    print("  battery 보유?", inv.has("battery"))         # True
    print("  uv_lamp 보유?", inv.has("uv_lamp"))         # False

    print("\n[4] 슬롯 가득 차면 추가 실패")
    inv.add("scope")
    inv.add("key")
    print("  추가 후:", inv, "가득?", inv.is_full())
    print("  하나 더 추가:", inv.add("note"))            # False

    print("\n[5] 사용 → 제거")
    print("  battery 제거:", inv.remove("battery"))      # True
    print("  battery 또 제거:", inv.remove("battery"))   # False
    print("  현재:", inv)

    print("\n[6] 직렬화")
    print("  to_list():", inv.to_list())
