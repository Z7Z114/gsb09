"""行为规格测试：逐条盯住 README「行为规格」的验收点。

这些用例在未修复的实现上应当失败，修复后通过。
"""
import asyncio
import json
import os
import time

import pytest


def _wait_until_disconnected(manager, timeout=2.0):
    # 服务端在子任务里异步处理断开，轮询等待摘除完成
    deadline = time.time() + timeout
    while manager.active_connections and time.time() < deadline:
        time.sleep(0.01)


# ---------- A. 请求校验与错误语义 ----------

@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_craftsman_blank_name_rejected(client, blank):
    resp = client.post("/api/craftsmen/", json={"name": blank, "school": "汉族传统弓"})
    assert resp.status_code == 422


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_message_blank_content_rejected(client, blank):
    resp = client.post("/api/messages/", json={"content": blank})
    assert resp.status_code == 422


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_wood_blank_name_rejected(client, blank):
    resp = client.post("/api/materials/woods", json={"name": blank})
    assert resp.status_code == 422


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_bow_part_blank_name_rejected(client, blank):
    resp = client.post("/api/materials/bow-parts", json={"name": blank})
    assert resp.status_code == 422


def test_craftsman_name_is_stripped(client):
    resp = client.post("/api/craftsmen/", json={"name": "  杨福喜  ", "school": "汉族传统弓"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "杨福喜"


@pytest.mark.parametrize("params", [{"skip": -1}, {"limit": 0}, {"limit": -5}, {"limit": 201}])
@pytest.mark.parametrize("path", [
    "/api/craftsmen/", "/api/messages/", "/api/materials/woods",
    "/api/materials/bow-parts", "/api/audio/recordings", "/api/archives/",
])
def test_pagination_out_of_range_rejected(client, path, params):
    resp = client.get(path, params=params)
    assert resp.status_code == 422


def test_pagination_within_range_ok(client):
    resp = client.get("/api/craftsmen/", params={"skip": 0, "limit": 1})
    assert resp.status_code == 200


def test_missing_resources_return_404(client):
    assert client.get("/api/craftsmen/9999").status_code == 404
    assert client.get("/api/messages/9999").status_code == 404
    assert client.get("/api/materials/woods/9999").status_code == 404
    assert client.get("/api/materials/bow-parts/9999").status_code == 404
    assert client.get("/api/audio/recordings/9999").status_code == 404
    assert client.get("/api/archives/9999").status_code == 404


# ---------- B. 数据完整性 ----------

def test_message_with_missing_craftsman_rejected(client):
    resp = client.post("/api/messages/", json={"content": "悬空消息", "craftsman_id": 9999})
    assert resp.status_code == 404
    contents = [m["content"] for m in client.get("/api/messages/").json()]
    assert "悬空消息" not in contents


def test_anonymous_message_allowed(client):
    resp = client.post("/api/messages/", json={"content": "匿名发言", "craftsman_id": None})
    assert resp.status_code == 200
    assert resp.json()["craftsman_id"] is None


def test_delete_craftsman_leaves_no_dangling_messages(client):
    craftsman = client.post("/api/craftsmen/", json={"name": "某匠人", "school": "满族清弓"}).json()
    client.post("/api/messages/", json={"content": "训弓心得", "craftsman_id": craftsman["id"]})

    client.delete(f"/api/craftsmen/{craftsman['id']}")

    messages = client.get("/api/messages/").json()
    owned = [m for m in messages if m["content"] == "训弓心得"]
    assert len(owned) == 1
    assert owned[0]["craftsman_id"] is None
    assert owned[0]["craftsman"] is None


def test_seed_data_idempotent(client):
    first = client.post("/api/materials/seed-data").json()
    assert first["woods_added"] is True
    assert first["bow_parts_added"] is True
    assert first["craftsmen_added"] is True

    woods_count = len(client.get("/api/materials/woods").json())
    parts_count = len(client.get("/api/materials/bow-parts").json())
    craftsmen_count = len(client.get("/api/craftsmen/").json())

    second = client.post("/api/materials/seed-data").json()
    assert second["woods_added"] is False
    assert second["bow_parts_added"] is False
    assert second["craftsmen_added"] is False

    assert len(client.get("/api/materials/woods").json()) == woods_count
    assert len(client.get("/api/materials/bow-parts").json()) == parts_count
    assert len(client.get("/api/craftsmen/").json()) == craftsmen_count


# ---------- C. 录音上传 ----------

@pytest.mark.parametrize("filename", ["evil.exe", "script.sh", "noext", "archive.tar.gz"])
def test_upload_rejects_disallowed_file_types(client, filename):
    resp = client.post("/api/audio/upload",
                       files={"file": (filename, b"MZ\x90\x00", "application/octet-stream")})
    assert resp.status_code == 400


def test_upload_without_file_returns_422(client):
    resp = client.post("/api/audio/upload")
    assert resp.status_code == 422


def test_upload_sanitizes_path_components(client):
    resp = client.post("/api/audio/upload",
                       files={"file": ("../../etc/passwd.wav", b"RIFF....WAVEfmt ", "audio/wav")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["filename"] == "passwd.wav"
    assert ".." not in body["path"]
    upload_root = os.path.realpath("uploads")
    assert os.path.realpath(os.path.dirname(body["path"])) == upload_root


def test_upload_keeps_original_chinese_filename(client):
    resp = client.post("/api/audio/upload",
                       files={"file": ("木工坊讨论录音.mp3", b"ID3", "audio/mpeg")})
    assert resp.status_code == 200
    assert resp.json()["filename"] == "木工坊讨论录音.mp3"


@pytest.mark.parametrize("filename", ["a.wav", "b.mp3", "c.m4a", "d.flac", "e.aac", "f.ogg"])
def test_upload_accepts_whitelisted_extensions(client, filename):
    resp = client.post("/api/audio/upload",
                       files={"file": (filename, b"data", "application/octet-stream")})
    assert resp.status_code == 200


# ---------- D. 实时消息（WebSocket） ----------

def test_websocket_invalid_json_gets_error_and_survives(client):
    from app.api.messages import manager

    with client.websocket_connect("/api/messages/ws") as ws:
        ws.send_text("这不是JSON")
        error = ws.receive_json()
        assert error["type"] == "error"

        ws.send_text(json.dumps({"content": "合法消息"}))
        broadcast = ws.receive_json()
        assert broadcast["content"] == "合法消息"

    _wait_until_disconnected(manager)
    assert len(manager.active_connections) == 0


def test_websocket_disconnect_removes_connection(client):
    from app.api.messages import manager

    with client.websocket_connect("/api/messages/ws"):
        assert len(manager.active_connections) == 1
    _wait_until_disconnected(manager)
    assert len(manager.active_connections) == 0


def test_broadcast_immune_to_single_bad_connection():
    from app.api.messages import ConnectionManager

    class FakeWebSocket:
        def __init__(self, broken=False):
            self.broken = broken
            self.received = []

        async def send_json(self, data):
            if self.broken:
                raise RuntimeError("connection already closed")
            self.received.append(data)

    async def scenario():
        manager = ConnectionManager()
        good_first, bad, good_last = FakeWebSocket(), FakeWebSocket(broken=True), FakeWebSocket()
        manager.active_connections = [good_first, bad, good_last]

        await manager.broadcast({"content": "广播消息"})

        assert good_first.received == [{"content": "广播消息"}]
        assert good_last.received == [{"content": "广播消息"}]
        assert bad not in manager.active_connections
        assert len(manager.active_connections) == 2

        # 重复摘除不得抛异常
        manager.disconnect(good_first)
        manager.disconnect(good_first)
        assert len(manager.active_connections) == 1

    asyncio.run(scenario())


# ---------- E. 工艺档案与邮件 ----------

def _make_transcribed_recording(client):
    from app.database import SessionLocal
    from app import models

    db = SessionLocal()
    recording = models.AudioRecording(
        filename="讨论.wav", original_path="uploads/x.wav", status="transcribed"
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)
    db.add(models.Transcript(
        recording_id=recording.id, content="胎角比例很关键", start_time=0.0, end_time=1.0
    ))
    db.commit()
    recording_id = recording.id
    db.close()
    return recording_id


def test_generate_archive_requires_transcribed_status(client):
    resp = client.post("/api/audio/upload",
                       files={"file": ("讨论.wav", b"RIFF....WAVEfmt ", "audio/wav")})
    recording_id = resp.json()["recording_id"]
    resp = client.post(f"/api/archives/generate/{recording_id}")
    assert resp.status_code == 400


def test_offline_archive_summary_carries_fallback_marker(client):
    recording_id = _make_transcribed_recording(client)
    resp = client.post(f"/api/archives/generate/{recording_id}")
    assert resp.status_code == 200

    archives = client.get("/api/archives/").json()
    assert len(archives) == 1
    assert archives[0]["content"].get("is_fallback") is True


def test_archive_service_fallback_marked_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from app.services.archive_service import ArchiveService

    service = ArchiveService()
    result = service.generate_archive_summary(
        [{"content": "讨论胎角比例", "speaker_label": "S1", "predicted_school": "汉族传统弓"}],
        [], {}
    )
    assert result.get("is_fallback") is True


def test_archive_service_openai_failure_propagates(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from app.services.archive_service import ArchiveService

    class BrokenCompletions:
        @staticmethod
        def create(**kwargs):
            raise RuntimeError("429 Too Many Requests")

    class BrokenChat:
        completions = BrokenCompletions()

    class BrokenClient:
        chat = BrokenChat()

    service = ArchiveService()
    service.client = BrokenClient()

    with pytest.raises(RuntimeError):
        service.generate_archive_summary(
            [{"content": "讨论胎角比例", "speaker_label": "S1", "predicted_school": "汉族传统弓"}],
            [], {}
        )


def test_send_email_not_marked_when_delivery_fails(client):
    from app.database import SessionLocal
    from app import models

    db = SessionLocal()
    archive = models.CraftArchive(
        title="角弓制作工艺档案", summary="摘要", content={}, keywords=[]
    )
    db.add(archive)
    db.commit()
    db.refresh(archive)
    archive_id = archive.id
    db.close()

    resp = client.post("/api/archives/send-email", json={"archive_id": archive_id})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False

    detail = client.get(f"/api/archives/{archive_id}").json()
    assert detail["sent_to_feiyi"] == 0
    assert detail["sent_at"] is None


def test_send_email_marks_sent_only_on_real_success(client, monkeypatch):
    from app.database import SessionLocal
    from app import models
    from app.services import email_service as email_module

    db = SessionLocal()
    archive = models.CraftArchive(
        title="角弓制作工艺档案", summary="摘要", content={}, keywords=[]
    )
    db.add(archive)
    db.commit()
    db.refresh(archive)
    archive_id = archive.id
    db.close()

    async def fake_send(*args, **kwargs):
        return {"success": True, "message": "Email sent successfully",
                "recipient": "feiyi@example.org"}

    monkeypatch.setattr(email_module.email_service, "send_archive_email", fake_send)

    resp = client.post("/api/archives/send-email", json={"archive_id": archive_id})
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    detail = client.get(f"/api/archives/{archive_id}").json()
    assert detail["sent_to_feiyi"] == 1
    assert detail["sent_at"] is not None


# ---------- F. 不得回归的既有正确行为 ----------

def test_predict_school_deterministic_and_explainable():
    from app.services.diarization_service import diarization_service

    result = diarization_service.predict_school("蒙古骑射短弓，也提到清弓", "SPEAKER_0")
    assert result["predicted_school"] == "蒙古族角弓"
    assert result["confidence"] == pytest.approx(3 / 4)

    unknown = diarization_service.predict_school("今天天气不错", "SPEAKER_0")
    assert unknown["predicted_school"] == "未知流派"
    assert unknown["confidence"] == 0


def test_extract_keywords_categories_unchanged():
    from app.services.transcription_service import transcription_service

    keywords = transcription_service.extract_keywords("桦木弓胎刨削训弓比例与传承")
    categories = {k["keyword"]: k["category"] for k in keywords}
    assert categories["桦木"] == "材料"
    assert categories["刨削"] == "工艺"
    assert categories["弓胎"] == "结构"
    assert categories["训弓"] == "技术"
    assert categories["传承"] == "其他"
