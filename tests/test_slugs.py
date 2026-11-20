from app.extensions import db
from app.models import Service
from app.services.slugs import slugify, unique_slug


def test_slugify_transliterates_cyrillic():
    assert slugify("Привет, мир!") == "privet-mir"


def test_slugify_handles_spaces_and_symbols():
    assert slugify("  UX/UI  дизайн  ") == "ux-ui-dizayn"


def test_slugify_empty_value():
    assert slugify("") == "item"
    assert slugify("!!!") == "item"


def test_slugify_respects_max_length():
    assert len(slugify("a" * 300)) <= 120


def test_unique_slug_adds_suffix(app, demo):
    with app.app_context():
        assert unique_slug(Service, "Стратегия и исследование") == (
            "strategiya-i-issledovanie-2"
        )


def test_unique_slug_excludes_current_record(app, demo):
    with app.app_context():
        service = Service.query.filter_by(slug="veb-razrabotka").one()
        assert unique_slug(Service, service.title, service.id) == service.slug
