import pytest

from app import create_app
from app.extensions import db
from app.models import Lead, Service
from config import TestConfig

VALID_LEAD = {
    "name": "Иван Петров",
    "contact": "ivan@example.com",
    "service_id": 0,
    "message": "Нужен сайт для студии, сроки — около месяца.",
}


def test_valid_lead_is_saved(client, app):
    response = client.post("/contacts", data=VALID_LEAD)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/contacts/success")

    with app.app_context():
        lead = Lead.query.one()
        assert lead.name == "Иван Петров"
        assert lead.status == "new"
        assert lead.service_id is None


def test_invalid_lead_shows_errors(client, app):
    response = client.post(
        "/contacts",
        data={"name": "", "contact": "", "service_id": 0, "message": ""},
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Укажите имя." in body
    assert "Опишите задачу." in body
    assert 'aria-invalid="true"' in body

    with app.app_context():
        assert Lead.query.count() == 0


def test_message_length_limit(client, app):
    data = dict(VALID_LEAD, message="а" * 2001)
    response = client.post("/contacts", data=data)

    assert response.status_code == 200
    assert "от 10 до 2000" in response.get_data(as_text=True)

    with app.app_context():
        assert Lead.query.count() == 0


def test_honeypot_blocks_saving(client, app):
    data = dict(VALID_LEAD, website="http://spam.example")
    response = client.post("/contacts", data=data)

    assert response.status_code == 302
    with app.app_context():
        assert Lead.query.count() == 0


def test_service_is_preselected_from_query(client, demo, app):
    with app.app_context():
        service_id = Service.query.filter_by(slug="veb-razrabotka").one().id

    html = client.get("/contacts?service=veb-razrabotka").get_data(as_text=True)
    assert f'<option selected value="{service_id}">' in html


def test_lead_can_be_linked_to_service(client, demo, app):
    with app.app_context():
        service_id = Service.query.filter_by(slug="veb-razrabotka").one().id

    data = dict(VALID_LEAD, service_id=service_id)
    client.post("/contacts", data=data)

    with app.app_context():
        assert Lead.query.one().service_id == service_id


def test_success_page_renders(client):
    response = client.get("/contacts/success")
    assert response.status_code == 200
    assert "Заявка отправлена" in response.get_data(as_text=True)


def test_csrf_is_enforced():
    class CsrfConfig(TestConfig):
        WTF_CSRF_ENABLED = True

    app = create_app(CsrfConfig)
    with app.app_context():
        db.create_all()
        try:
            response = app.test_client().post("/contacts", data=VALID_LEAD)
            assert response.status_code == 400
        finally:
            db.session.remove()
            db.drop_all()
