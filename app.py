"""
폐연구실 탈출 게임 - 백엔드 진입점.
Flask 서버를 실행하는 메인 파일.
"""
from flask import Flask, jsonify
from flask_cors import CORS


# Flask 앱 생성
app = Flask(__name__)
# 한글 응답을 유니코드 이스케이프 없이 그대로 내보내도록 설정
app.json.ensure_ascii = False
# 프론트엔드(다른 포트)에서도 호출할 수 있도록 CORS 허용
CORS(app)


@app.route("/")
def health():
    """헬스체크 - 서버가 살아있는지 확인하는 엔드포인트."""
    return jsonify({
        "success": True,
        "message": "폐연구실 탈출 게임 백엔드 정상 작동 중",
    })


if __name__ == "__main__":
    # debug=True : 코드 수정 시 서버 자동 재시작
    # host="0.0.0.0" : 같은 네트워크 다른 기기에서도 접근 가능
    # 참고: Mac은 5000번 포트를 AirPlay가 사용하므로 5050으로 설정
    app.run(host="0.0.0.0", port=5050, debug=True)
