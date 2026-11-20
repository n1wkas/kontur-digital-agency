import pytest

from app import create_app
from app.extensions import db
from app.models import AdminUser
from app.services.seed import seed_demo_data
from config import TestConfig


@pytest.fixture
def app(tmp_path):
    class Config(TestConfig):
        UPLOAD_FOLDER = str(tmp_path / "uploads")

    application = create_app(Config)

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def demo(app):
    seed_demo_data()


@pytest.fixture
def admin_user(app):
    user = AdminUser(username="admin")
    user.set_password("secret123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def auth_client(client, admin_user):
    client.post(
        "/admin/login",
        data={"username": "admin", "password": "secret123"},
    )
    return client
