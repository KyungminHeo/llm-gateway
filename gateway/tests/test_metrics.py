"""
메트릭 & 헬스체크 테스트
"""


def test_헬스체크(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_메트릭_조회(client):
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "avg_response_time_ms" in data
    assert "by_status" in data
    assert "slowest_top5" in data
