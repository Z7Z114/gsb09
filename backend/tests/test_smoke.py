"""冒烟测试：只覆盖顺利路径。

这些用例在初始快照上应当全绿；它们不覆盖 README「行为规格」里的边界语义，
因此通过它们并不代表规格已被满足。
"""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_root_lists_endpoints(client):
    body = client.get("/").json()
    assert body["name"] == "弓道纪要 API"
    assert "craftsmen" in body["endpoints"]


def test_seed_then_query_materials(client):
    resp = client.post("/api/materials/seed-data")
    assert resp.status_code == 200
    assert resp.json()["message"]

    woods = client.get("/api/materials/woods").json()
    assert len(woods) > 0

    parts = client.get("/api/materials/bow-parts").json()
    assert len(parts) > 0


def test_craftsman_crud_flow(client):
    created = client.post("/api/craftsmen/", json={"name": "杨福喜", "school": "汉族传统弓"})
    assert created.status_code == 200
    craftsman_id = created.json()["id"]

    detail = client.get(f"/api/craftsmen/{craftsman_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == "杨福喜"

    updated = client.put(f"/api/craftsmen/{craftsman_id}",
                         json={"name": "杨福喜", "school": "汉族传统弓", "generation": 7})
    assert updated.status_code == 200
    assert updated.json()["generation"] == 7

    deleted = client.delete(f"/api/craftsmen/{craftsman_id}")
    assert deleted.status_code == 200
    assert client.get(f"/api/craftsmen/{craftsman_id}").status_code == 404


def test_message_flow(client):
    created = client.post("/api/messages/", json={"content": "今天讨论胎角比例", "craftsman_id": None})
    assert created.status_code == 200

    listing = client.get("/api/messages/")
    assert listing.status_code == 200
    assert any(m["content"] == "今天讨论胎角比例" for m in listing.json())


def test_audio_upload_and_list(client):
    resp = client.post("/api/audio/upload",
                       files={"file": ("讨论.wav", b"RIFF....WAVEfmt ", "audio/wav")})
    assert resp.status_code == 200
    recording_id = resp.json()["recording_id"]

    detail = client.get(f"/api/audio/recordings/{recording_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "uploaded"

    listing = client.get("/api/audio/recordings")
    assert listing.status_code == 200


def test_archive_html_export(client):
    from app.database import SessionLocal
    from app import models

    db = SessionLocal()
    archive = models.CraftArchive(
        title="角弓制作工艺档案",
        summary="本次交流聚焦胎角比例与训弓技巧。",
        content={"key_points": ["胎角比例"], "school_analysis": {}, "heritage_value": "高"},
        keywords=["传统弓箭", "胎角"],
    )
    db.add(archive)
    db.commit()
    db.refresh(archive)
    archive_id = archive.id
    db.close()

    resp = client.get(f"/api/archives/{archive_id}/html")
    assert resp.status_code == 200
    assert resp.json()["html_content"]
