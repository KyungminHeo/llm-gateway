"""
대화 관리 API 테스트
"""


def test_대화_생성(client, auth_headers):
    response = client.post(
        "/api/conversations/",
        json={"title": "테스트 대화"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["title"] == "테스트 대화"
    assert "id" in response.json()


def test_대화_목록_조회(client, auth_headers):
    client.post("/api/conversations/", json={"title": "목록테스트"}, headers=auth_headers)

    response = client.get("/api/conversations/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_대화_상세_및_삭제(client, auth_headers):
    # 생성
    create_resp = client.post(
        "/api/conversations/",
        json={"title": "삭제 테스트"},
        headers=auth_headers,
    )
    conv_id = create_resp.json()["id"]

    # 상세 조회
    detail_resp = client.get(f"/api/conversations/{conv_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["title"] == "삭제 테스트"
    assert "messages" in detail_resp.json()

    # 삭제
    delete_resp = client.delete(f"/api/conversations/{conv_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    # 삭제 후 404
    gone_resp = client.get(f"/api/conversations/{conv_id}", headers=auth_headers)
    assert gone_resp.status_code == 404


def test_인증_없이_접근_차단(client):
    response = client.get("/api/conversations/")
    assert response.status_code in [401, 403]
