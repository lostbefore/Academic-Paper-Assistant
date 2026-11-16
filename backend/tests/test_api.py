"""HTTP API behaviour: auth, ownership, CRUD, exports and health."""

from __future__ import annotations

import uuid

from app import db


def _insert_completed_paper(user_id: str, title: str = "测试论文标题") -> str:
    paper_id = f"p_test_{uuid.uuid4().hex[:8]}"
    now = db.utcnow()
    sections = {
        "title": title,
        "abstract": "摘要内容。" * 20,
        "introduction": "引言内容。" * 40,
        "literature_review": "综述内容。" * 40,
        "methodology": "方法内容。" * 40,
        "results": "结果内容。" * 40,
        "discussion": "讨论内容。" * 40,
        "conclusion": "结论内容。" * 20,
        "references": "[1] 测试作者. 测试文献[J]. 测试期刊, 2024.",
    }
    db.execute(
        """INSERT INTO papers
           (id, user_id, title, status, stage, progress, request_json, outline_json,
            sections_json, refs_json, meta_json, error, created_at, updated_at, finished_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            paper_id, user_id, title, "completed", "completed", 100,
            db.dumps({"title": title, "language": "zh", "citation_style": "gbt7714", "keywords": ["测试"]}),
            db.dumps({"title": title, "sections": []}),
            db.dumps(sections),
            db.dumps([{"title": "测试文献", "authors": ["测试作者"], "year": 2024, "venue": "测试期刊"}]),
            db.dumps({"word_count": 400, "model": "test-model"}),
            "", now, now, now,
        ),
    )
    return paper_id


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] == "ok"
    assert body["version"] == "2.0.0"


def test_status_never_leaks_the_api_key(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    body = response.json()
    assert "test-placeholder-key" not in str(body)
    assert body["llm_configured"] is True


def test_papers_require_authentication(client):
    assert client.get("/api/papers").status_code == 401
    assert client.get("/api/stats").status_code == 401


def test_register_and_login(client):
    email = f"user{uuid.uuid4().hex[:6]}@test.local"
    registered = client.post(
        "/api/auth/register", json={"email": email, "password": "GoodPass123", "name": "测试用户"}
    )
    assert registered.status_code == 201
    token = registered.json()["access_token"]
    assert registered.json()["user"]["email"] == email

    duplicate = client.post(
        "/api/auth/register", json={"email": email, "password": "GoodPass123", "name": "x"}
    )
    assert duplicate.status_code == 409

    login = client.post("/api/auth/login", json={"email": email, "password": "GoodPass123"})
    assert login.status_code == 200
    assert login.json()["access_token"]

    wrong = client.post("/api/auth/login", json={"email": email, "password": "wrong-pass"})
    assert wrong.status_code == 401

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_create_paper_validates_input(client, auth_headers):
    response = client.post("/api/papers", headers=auth_headers, json={"title": "x"})
    assert response.status_code == 422


def test_paper_lifecycle(client, auth_headers, admin_token):
    me = client.get("/api/auth/me", headers=auth_headers).json()
    paper_id = _insert_completed_paper(me["id"], "生命周期测试论文")

    detail = client.get(f"/api/papers/{paper_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["sections"]["abstract"].startswith("摘要内容")

    listing = client.get("/api/papers", headers=auth_headers)
    assert any(p["id"] == paper_id for p in listing.json())

    stats = client.get("/api/stats", headers=auth_headers)
    assert stats.json()["total"] >= 1

    patched = client.patch(
        f"/api/papers/{paper_id}", headers=auth_headers, json={"title": "改名后的论文"}
    )
    assert patched.status_code == 200
    assert patched.json()["title"] == "改名后的论文"

    section = client.put(
        f"/api/papers/{paper_id}/sections/discussion",
        headers=auth_headers,
        json={"content": "人工修改后的讨论段落。"},
    )
    assert section.status_code == 200
    assert section.json()["sections"]["discussion"] == "人工修改后的讨论段落。"

    for fmt, signature in (("docx", b"PK"), ("pdf", b"%PDF"), ("md", b"#"), ("bib", b"@article")):
        exported = client.get(f"/api/papers/{paper_id}/export/{fmt}", headers=auth_headers)
        assert exported.status_code == 200, fmt
        assert exported.content.startswith(signature), fmt

    deleted = client.delete(f"/api/papers/{paper_id}", headers=auth_headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/papers/{paper_id}", headers=auth_headers).status_code == 404


def test_other_users_cannot_read_someone_elses_paper(client, admin_token):
    owner = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"}).json()
    paper_id = _insert_completed_paper(owner["id"], "私有论文")

    email = f"other{uuid.uuid4().hex[:6]}@test.local"
    other = client.post(
        "/api/auth/register", json={"email": email, "password": "GoodPass123", "name": "别人"}
    ).json()["access_token"]
    response = client.get(f"/api/papers/{paper_id}", headers={"Authorization": f"Bearer {other}"})
    assert response.status_code == 403

    client.delete(f"/api/papers/{paper_id}", headers={"Authorization": f"Bearer {admin_token}"})


def test_export_requires_completed_status(client, auth_headers, admin_token):
    owner = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"}).json()
    paper_id = f"p_run_{uuid.uuid4().hex[:8]}"
    now = db.utcnow()
    db.execute(
        """INSERT INTO papers (id, user_id, title, status, stage, progress, request_json,
           outline_json, sections_json, refs_json, meta_json, error, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (paper_id, owner["id"], "进行中的论文", "running", "writing", 40, "{}", "{}", "{}", "[]", "{}", "", now, now),
    )
    response = client.get(f"/api/papers/{paper_id}/export/pdf", headers=auth_headers)
    assert response.status_code == 409
    db.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
