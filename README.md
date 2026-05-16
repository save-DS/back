# 폐연구실 탈출 게임 - 백엔드

자료구조 수업 프로젝트. Flask 기반 게임 백엔드.

## 설치

### 1) 가상환경 만들기 (권장)
```bash
python3 -m venv venv
source venv/bin/activate    # Mac / Linux
# venv\Scripts\activate     # Windows
```

### 2) 패키지 설치
```bash
pip install -r requirements.txt
```

## 실행

```bash
python app.py
```

서버는 `http://localhost:5050` 에서 실행된다.
브라우저에서 `http://localhost:5050/` 접속해서 헬스체크 응답이 보이면 성공.

> Mac은 5000번 포트를 AirPlay Receiver가 사용하므로 5050번을 쓴다.

```json
{
  "success": true,
  "message": "폐연구실 탈출 게임 백엔드 정상 작동 중"
}
```

## 폴더 구조

```
back/
├── app.py                  # Flask 진입점
├── requirements.txt        # 의존성 목록
├── .gitignore
├── README.md
│
├── api/                    # API 라우터 (Phase 3 이후 채워짐)
├── data/                   # 정적 JSON 데이터
│   ├── rooms.json          # 방/시점 구조
│   ├── items.json          # 아이템 정의
│   ├── objects.json        # 클릭 가능한 오브젝트
│   └── puzzles.json        # 퍼즐 정답/단서
│
├── services/               # 게임 로직 모듈
│   └── game_state.py       # 게임 상태 (싱글톤)
│
└── utils/                  # 헬퍼
    └── data_loader.py      # JSON 로더
```

## 자료구조 사용

| 자료구조 | 사용처 |
|---------|--------|
| 딕셔너리 | JSON 데이터, GameState 전체 |
| 리스트 | 인벤토리, 단서, 시점별 오브젝트 |
| 셋 | 해결한 퍼즐, 조사한 오브젝트 (중복 방지) |
| 스택 | 화면 히스토리 (뒤로가기) |
| 큐 | 이벤트 큐 |
| 그래프 | 방 연결 (Phase 2 이후) |
| BFS | 미로 최단 경로 (Phase 2 이후) |

## 모듈 단독 테스트

각 모듈은 `python -m` 으로 단독 실행할 수 있다.

```bash
# 데이터 로딩 테스트
python -m utils.data_loader

# GameState 동작 테스트
python -m services.game_state
```
