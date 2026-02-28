"""
인증 관련 테스트
"""
import uuid
from service.auth_service import get_password_hash, verify_password


# ===== 단위 테스트 =====

def test_비밀번호_해싱_성공():
    password = "MyPassword123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert len(hashed) > 0


def test_비밀번호_검증_성공():
    password = "MyPassword123!"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True


def test_비밀번호_검증_실패():
    hashed = get_password_hash("correct")
    assert verify_password("wrong", hashed) is False


# ===== API 테스트 =====

def test_회원가입_성공(client):
    unique = uuid.uuid4().hex[:6]
    response = client.post("/api/auth/register", json={
        "username": f"signup_{unique}",
        "email": f"signup_{unique}@example.com",
        "password": "Strong1234!",
    })
    assert response.status_code == 201
    assert response.json()["username"] == f"signup_{unique}"


def test_회원가입_중복_이메일(client):
    """같은 이메일로 두 번 가입하면 400"""
    unique = uuid.uuid4().hex[:6]
    client.post("/api/auth/register", json={
        "username": f"dup1_{unique}",
        "email": f"dup_{unique}@example.com",
        "password": "Test1234!",
    })
    # 같은 이메일로 다시 가입 시도
    response = client.post("/api/auth/register", json={
        "username": f"dup2_{unique}",
        "email": f"dup_{unique}@example.com",
        "password": "Test1234!",
    })
    assert response.status_code == 400
