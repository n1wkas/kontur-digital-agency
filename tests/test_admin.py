import base64
import io
from pathlib import Path

from app.extensions import db
from app.models import Lead, Project, Service

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

ADMIN_PATHS = [
    "/admin/",
    "/admin/services",
    "/admin/projects",
    "/admin/testimonials",
    "/admin/leads",
]


def test_admin_requires_login(client):
    for path in ADMIN_PATHS:
        response = client.get(path)
        assert response.status_code == 302
        assert "/admin/login" in response.headers["Location"]


def test_login_and_logout(client, admin_user):
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "secret123"},
    )
    assert response.status_code == 302
    assert "/admin/" in response.headers["Location"]
    assert client.get("/admin/").status_code == 200

    response = client.post("/admin/logout")
    assert response.status_code == 302
    assert client.get("/admin/").status_code == 302


def test_wrong_password_is_rejected(client, admin_user):
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "nope"},
    )
    assert response.status_code == 200
    assert "Неверный логин или пароль." in response.get_data(as_text=True)


def test_login_next_rejects_external_url(client, admin_user):
    response = client.post(
        "/admin/login?next=//evil.example",
        data={"username": "admin", "password": "secret123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/")


def test_admin_lists_render(auth_client, demo):
    for path in ADMIN_PATHS:
        assert auth_client.get(path).status_code == 200


def test_service_crud(auth_client, app):
    response = auth_client.post(
        "/admin/services/new",
        data={"title": "Новая услуга", "slug": "", "sort_order": 5, "is_published": "y"},
    )
    assert response.status_code == 302

    with app.app_context():
        service = Service.query.one()
        assert service.slug == "novaya-usluga"
        assert service.is_published is True
        service_id = service.id

    response = auth_client.post(
        f"/admin/services/{service_id}/edit",
        data={"title": "Обновлённая услуга", "slug": "", "sort_order": 7, "is_published": "y"},
    )
    assert response.status_code == 302
    with app.app_context():
        service = db.session.get(Service, service_id)
        assert service.title == "Обновлённая услуга"
        assert service.sort_order == 7

    auth_client.post(f"/admin/services/{service_id}/toggle")
    with app.app_context():
        assert db.session.get(Service, service_id).is_published is False

    auth_client.post(f"/admin/services/{service_id}/delete")
    with app.app_context():
        assert db.session.get(Service, service_id) is None


def test_duplicate_slug_is_rejected(auth_client, app):
    auth_client.post(
        "/admin/services/new",
        data={"title": "Первая", "slug": "", "sort_order": 0, "is_published": "y"},
    )

    response = auth_client.post(
        "/admin/services/new",
        data={"title": "Вторая", "slug": "pervaya", "sort_order": 0, "is_published": "y"},
    )

    assert response.status_code == 200
    assert "Такой slug уже используется." in response.get_data(as_text=True)
    with app.app_context():
        assert Service.query.count() == 1


def test_manual_slug_is_normalized(auth_client, app):
    auth_client.post(
        "/admin/services/new",
        data={"title": "Услуга", "slug": "Мой Slug!", "sort_order": 0, "is_published": "y"},
    )
    with app.app_context():
        assert Service.query.one().slug == "moy-slug"


def test_project_image_upload_and_delete(auth_client, app):
    data = {
        "title": "Кейс с картинкой",
        "slug": "",
        "category": "Тест",
        "summary": "summary",
        "is_published": "y",
        "image": (io.BytesIO(PNG), "cover.png"),
    }
    response = auth_client.post(
        "/admin/projects/new",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 302

    with app.app_context():
        project = Project.query.one()
        project_id = project.id
        image_name = project.image_path
        image_path = Path(app.config["UPLOAD_FOLDER"]) / image_name

    assert image_name is not None
    assert image_path.is_file()
    assert auth_client.get(f"/media/{image_name}").status_code == 200

    auth_client.post(f"/admin/projects/{project_id}/delete")
    assert not image_path.exists()


def test_project_rejects_non_image_upload(auth_client, app):
    data = {
        "title": "Кейс с плохим файлом",
        "slug": "",
        "summary": "summary",
        "is_published": "y",
        "image": (io.BytesIO(b"#!/bin/sh\necho hi"), "payload.sh"),
    }
    response = auth_client.post(
        "/admin/projects/new",
        data=data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert "Только JPG, PNG или WebP." in response.get_data(as_text=True)
    with app.app_context():
        assert Project.query.count() == 0
        assert list(Path(app.config["UPLOAD_FOLDER"]).glob("*")) == []


def test_project_rejects_oversized_image(auth_client, app):
    big = b"0" * (2 * 1024 * 1024 + 1)
    data = {
        "title": "Кейс с большим файлом",
        "slug": "",
        "summary": "summary",
        "is_published": "y",
        "image": (io.BytesIO(big), "big.png"),
    }
    response = auth_client.post(
        "/admin/projects/new",
        data=data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert "Файл больше 2 МБ." in response.get_data(as_text=True)
    with app.app_context():
        assert Project.query.count() == 0
        assert list(Path(app.config["UPLOAD_FOLDER"]).glob("*")) == []


def test_oversized_request_returns_413_page(auth_client, app):
    huge = b"0" * (4 * 1024 * 1024)
    data = {
        "title": "Кейс с огромным файлом",
        "slug": "",
        "summary": "summary",
        "is_published": "y",
        "image": (io.BytesIO(huge), "huge.png"),
    }
    response = auth_client.post(
        "/admin/projects/new",
        data=data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 413
    assert "Файл слишком большой" in response.get_data(as_text=True)
    with app.app_context():
        assert Project.query.count() == 0


def test_project_feature_toggle(auth_client, app):
    with app.app_context():
        project = Project(title="Кейс", slug="keys", is_published=True)
        db.session.add(project)
        db.session.commit()
        project_id = project.id

    auth_client.post(f"/admin/projects/{project_id}/feature")
    with app.app_context():
        assert db.session.get(Project, project_id).is_featured is True


def test_lead_status_update(auth_client, app):
    with app.app_context():
        lead = Lead(name="Клиент", contact="client@example.com", message="Нужен сайт.")
        db.session.add(lead)
        db.session.commit()
        lead_id = lead.id

    response = auth_client.post(f"/admin/leads/{lead_id}", data={"status": "done"})
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Lead, lead_id).status == "done"


def test_deleting_service_keeps_lead(auth_client, app):
    with app.app_context():
        service = Service(title="Услуга", slug="usluga", is_published=True)
        db.session.add(service)
        db.session.commit()
        lead = Lead(
            name="Клиент",
            contact="client@example.com",
            message="Нужен сайт.",
            service_id=service.id,
        )
        db.session.add(lead)
        db.session.commit()
        service_id = service.id
        lead_id = lead.id

    auth_client.post(f"/admin/services/{service_id}/delete")
    with app.app_context():
        assert db.session.get(Lead, lead_id).service_id is None
