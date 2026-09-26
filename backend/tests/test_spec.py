"""行为规格测试：逐条盯住 README「行为规格」的验收点。

这些用例在未修复的实现上应当失败，修复后通过。
"""
import asyncio
import json
import os
import time

import pytest


# ---------- A. 请求校验与错误语义 ----------

@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_craftsman_blank_name_rejected(client, blank):
    resp = client.post("/api/craftsmen/", json={"name": blank, "school": "汉族传统弓"})
    assert resp.status_code == 422


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_message_blank_content_rejected(client, blank):
    resp = client.post("/api/messages/", json={"content": blank, "craftsman_id": None})
    assert resp.status_code == 422


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_wood_blank_name_rejected(client, blank):
    resp = client.post("/api/materials/woods", json={"name": blank})
    assert resp.status_code == 422


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_bow_part_blank_name_rejected(client, blank):
    resp = client.post("/api/materials/bow-parts", json={"name": blank})
    assert resp.status_code == 422


def test_required_string_is_stripped(client):
    resp = client.post("/api/craftsmen/", json={"name": "  杨福喜  ", "school": "汉族传统弓"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "杨福喜"


@pytest.mark.parametrize("path", [
    "/api/craftsmen/",
    "/api/messages/",
    "/api/audio/recordings",
    "/api/archives/",
    "/api/materials/woods",
    "/api/materials/bow-parts",
])
def test_pagination_bounds(client, path):
    assert client.get(path, params={"skip": -1}).status_code == 422
    assert client.get(path, params={"limit": 0}).status_code == 422
    assert client.get(path, params={"limit": -5}).status_code == 422
    assert client.get(path, params={"limit": 201}).status_code == 422
    assert client.get(path, params={"skip": 0, "limit": 1}).status_code == 200


@pytest.mark.parametrize("path", [
    "/api/craftsmen/99999",
    "/api/messages/99999",
    "/api/audio/recordings/99999",
    "/api/archives/99999",
    "/api/materials/woods/99999",
    "/api/materials/bow-parts/99999",
])
def test_missing_resource_returns_404(client, path):
    resp = client.get(path)
    assert resp.status_code == 404
    assert resp.json()["detail"]


# ---------- B. 数据完整性 ----------

def test_message_with_unknown_craftsman_rejected(client):
    resp = client.post("/api/messages/", json={"content": "胎角比例", "craftsman_id": 99999})
    assert resp.status_code == 404
    listing = client.get("/api/messages/").json()
    assert all(m["craftsman_id"] != 99999 for m in listing)


def test_anonymous_message_allowed(client):
    resp = client.post("/api/messages/", json={"content": "匿名发言", "craftsman_id": None})
    assert resp.status_code == 200
    assert resp.json()["craftsman_id"] is None


def test_delete_craftsman_leaves_no_dangling_messages(client):
    craftsman = client.post("/api/craftsmen/", json={"name": "阿拉坦", "school": "蒙古族角弓"}).json()
    msg = client.post("/api/messages/",
                      json={"content": "骑射弓心得", "craftsman_id": craftsman["id"]}).json()

    assert client.delete(f"/api/craftsmen/{craftsman['id']}").status_code == 200

    listing = client.get("/api/messages/").json()
    kept = [m for m in listing if m["id"] == msg["id"]]
    assert kept, "消息不应被级联删除"
    assert kept[0]["craftsman_id"] is None, "不得留下指向已删除匠人的悬空引用"


def test_seed_data_is_idempotent(client):
    first = client.post("/api/materials/seed-data")
    assert first.status_code == 200
    assert first.json()["woods_added"] is True
    assert first.json()["bow_parts_added"] is True
    assert first.json()["craftsmen_added"] is True

    woods_before = len(client.get("/api/materials/woods").json())
    parts_before = len(client.get("/api/materials/bow-parts").json())
    craftsmen_before = len(client.get("/api/craftsmen/").json())

    second = client.post("/api/materials/seed-data")
    assert second.status_code == 200
    assert second.json()["woods_added"] is False
    assert second.json()["bow_parts_added"] is False
    assert second.json()["craftsmen_added"] is False

    assert len(client.get("/api/materials/woods").json()) == woods_before
    assert len(client.get("/api/materials/bow-parts").json()) == parts_before
    assert len(client.get("/api/craftsmen/").json()) == craftsmen_before


def test_seed_data_completes_partial_state_without_duplicates(client):
    client.post("/api/materials/woods", json={"name": "桦木", "origin": "手工录入"})

    resp = client.post("/api/materials/seed-data")
    assert resp.status_code == 200
    assert resp.json()["woods_added"] is True

    woods = client.get("/api/materials/woods", params={"limit": 200}).json()
    names = [w["name"] for w in woods]
    assert len(names) == len(set(names)), "不得产生重复记录"
    for expected in ["桦木", "橡木", "榆木", "桑木", "柘木"]:
        assert expected in names


# ---------- C. 录音上传 ----------

@pytest.mark.parametrize("filename", ["恶意.exe", "脚本.sh", "无扩展名", "archive.tar.gz"])
def test_upload_rejects_non_audio_files(client, filename):
    resp = client.post("/api/audio/upload", files={"file": (filename, b"data")})
    assert resp.status_code == 400


@pytest.mark.parametrize("filename", ["讨论.wav", "a.mp3", "b.m4a", "c.flac", "d.aac", "e.ogg", "F.WAV"])
def test_upload_accepts_audio_whitelist(client, filename):
    resp = client.post("/api/audio/upload", files={"file": (filename, b"data")})
    assert resp.status_code == 200


def test_upload_missing_file_returns_422(client):
    resp = client.post("/api/audio/upload")
    assert resp.status_code == 422


def test_upload_filename_sanitized(client):
    resp = client.post("/api/audio/upload",
                       files={"file": ("../../etc/passwd.wav", b"data")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["filename"] == "passwd.wav"
    assert "/" not in body["filename"] and "\\" not in body["filename"]

    real_path = os.path.realpath(body["path"])
    assert real_path.startswith(os.path.realpath("uploads") + os.sep)
    assert os.path.exists(real_path)


def test_upload_keeps_original_chinese_filename(client):
    resp = client.post("/api/audio/upload",
                       files={"file": ("木工坊讨论录音.wav", b"data")})
    assert resp.status_code == 200
    assert resp.json()["filename"] == "木工坊讨论录音.wav"


# ---------- D. 实时消息（WebSocket） ----------

def test_ws_invalid_json_does_not_kill_connection(client):
    with client.websocket_connect("/api/messages/ws") as ws:
        ws.send_text("这不是 JSON")
        err = ws.receive_json()
        assert "error" in err

        ws.send_text(json.dumps({"content": "胎角比例怎么定"}))
        msg = ws.receive_json()
        assert msg["content"] == "胎角比例怎么定"

    from app.api.messages import manager
    # TestClient 退出上下文后服务端异步处理断开，稍作等待再断言
    deadline = time.time() + 2
    while manager.active_connections and time.time() < deadline:
        time.sleep(0.05)
    assert len(manager.active_connections) == 0, "断开后连接不得残留"


def test_ws_unknown_craftsman_rejected(client):
    with client.websocket_connect("/api/messages/ws") as ws:
        ws.send_text(json.dumps({"content": "你好", "craftsman_id": 99999}))
        err = ws.receive_json()
        assert "error" in err


def test_broadcast_immune_to_single_bad_connection():
    from app.api.messages import ConnectionManager

    class FakeWebSocket:
        def __init__(self, fail=False):
            self.fail = fail
            self.received = []

        async def send_json(self, message):
            if self.fail:
                raise RuntimeError("connection closed")
            self.received.append(message)

    manager = ConnectionManager()
    good_first, bad, good_last = FakeWebSocket(), FakeWebSocket(fail=True), FakeWebSocket()
    manager.active_connections = [good_first, bad, good_last]

    asyncio.run(manager.broadcast({"content": "广播"}))

    assert good_first.received == [{"content": "广播"}]
    assert good_last.received == [{"content": "广播"}], "坏连接不得阻断后续连接"
    assert bad not in manager.active_connections, "坏连接必须被摘除"


def test_disconnect_is_idempotent():
    from app.api.messages import ConnectionManager

    manager = ConnectionManager()
    ws = object()
    manager.active_connections = [ws]
    manager.disconnect(ws)
    manager.disconnect(ws)  # 重复摘除不得抛异常
    assert manager.active_connections == []


# ---------- E. 工艺档案与邮件 ----------

def _transcripts():
    return [{"content": "胎角比例很关键，训弓要循序渐进", "speaker_label": "SPEAKER_00",
             "predicted_school": "汉族传统弓"}]


def test_summary_fallback_is_marked_when_no_api_key(client):
    from app.services.archive_service import archive_service

    assert archive_service.client is None, "未配置 OPENAI_API_KEY 时不应有真实客户端"
    result = archive_service.generate_archive_summary(_transcripts(), [], {})
    assert result.get("is_fallback") is True, "离线摘要必须带可识别标记"


def test_summary_real_call_failure_propagates(client, monkeypatch):
    from app.services.archive_service import archive_service

    class BrokenCompletions:
        def create(self, **kwargs):
            raise RuntimeError("429 Too Many Requests")

    class BrokenChat:
        completions = BrokenCompletions()

    class BrokenClient:
        chat = BrokenChat()

    monkeypatch.setattr(archive_service, "client", BrokenClient())
    with pytest.raises(RuntimeError):
        archive_service.generate_archive_summary(_transcripts(), [], {})


def _create_archive(client):
    from app.database import SessionLocal
    from app import models

    db = SessionLocal()
    archive = models.CraftArchive(
        title="角弓制作工艺档案",
        summary="胎角比例与训弓技巧。",
        content={"key_points": ["胎角比例"]},
        keywords=["传统弓箭"],
    )
    db.add(archive)
    db.commit()
    db.refresh(archive)
    archive_id = archive.id
    db.close()
    return archive_id


def test_send_email_not_configured_stays_unsent(client):
    archive_id = _create_archive(client)

    resp = client.post("/api/archives/send-email", json={"archive_id": archive_id})
    assert resp.status_code == 200
    assert resp.json()["success"] is False, "未配置邮件服务不得谎报成功"

    archive = client.get(f"/api/archives/{archive_id}").json()
    assert archive["sent_to_feiyi"] == 0
    assert archive["sent_at"] is None


def test_send_email_marks_sent_only_on_real_success(client, monkeypatch):
    from app.services.email_service import email_service

    async def fake_send(*args, **kwargs):
        return {"success": True, "message": "Email sent successfully", "recipient": "feiyi@example.org"}

    monkeypatch.setattr(email_service, "send_archive_email", fake_send)

    archive_id = _create_archive(client)
    resp = client.post("/api/archives/send-email", json={"archive_id": archive_id})
    assert resp.json()["success"] is True

    archive = client.get(f"/api/archives/{archive_id}").json()
    assert archive["sent_to_feiyi"] == 1
    assert archive["sent_at"] is not None


def test_send_email_delivery_failure_stays_unsent(client, monkeypatch):
    from app.services.email_service import email_service

    async def fake_send(*args, **kwargs):
        return {"success": False, "message": "Failed to send email: connection refused"}

    monkeypatch.setattr(email_service, "send_archive_email", fake_send)

    archive_id = _create_archive(client)
    resp = client.post("/api/archives/send-email", json={"archive_id": archive_id})
    assert resp.json()["success"] is False

    archive = client.get(f"/api/archives/{archive_id}").json()
    assert archive["sent_to_feiyi"] == 0
    assert archive["sent_at"] is None


def test_generate_archive_requires_transcribed_status(client):
    upload = client.post("/api/audio/upload",
                         files={"file": ("讨论.wav", b"RIFF....WAVEfmt ")}).json()
    resp = client.post(f"/api/archives/generate/{upload['recording_id']}")
    assert resp.status_code == 400


def test_generate_archive_unknown_recording_404(client):
    resp = client.post("/api/archives/generate/99999")
    assert resp.status_code == 404
