import re

from app.extensions import db
from app.models import Service

HREF_RE = re.compile(r'href="(/[^"#]*)"')

PUBLIC_PAGES = [
    "/",
    "/services",
    "/portfolio",
    "/about",
    "/contacts",
]


def test_home_shows_seeded_content(client, demo):
    html = client.get("/").get_data(as_text=True)
    assert "Стратегия и исследование" in html
    assert "Северный свет" in html
    assert "Демонстрационный проект" in html


def test_services_list_and_detail(client, demo):
    assert client.get("/services").status_code == 200

    html = client.get("/services/veb-razrabotka").get_data(as_text=True)
    assert "Веб-разработка" in html
    assert "Что входит" in html


def test_unpublished_service_is_hidden(app, client):
    with app.app_context():
        db.session.add(
            Service(
                title="Скрытая услуга",
                slug="skrytaya",
                is_published=False,
            )
        )
        db.session.commit()

    html = client.get("/services").get_data(as_text=True)
    assert "Скрытая услуга" not in html
    assert client.get("/services/skrytaya").status_code == 404


def test_portfolio_category_filter(client, demo):
    html = client.get("/portfolio?category=E-commerce").get_data(as_text=True)
    assert "Тихий двор" in html
    assert "Северный свет" not in html


def test_project_detail_shows_case_sections_and_demo_note(client, demo):
    html = client.get("/portfolio/severnyy-svet").get_data(as_text=True)
    assert "Задача" in html
    assert "Решение" in html
    assert "Результат" in html
    assert "вымышленный пример" in html


def test_unknown_slugs_return_404(client, demo):
    assert client.get("/services/net-takoy").status_code == 404
    assert client.get("/portfolio/net-takogo").status_code == 404


def test_about_and_contacts_render(client, demo):
    about = client.get("/about").get_data(as_text=True)
    assert "Команда" in about
    assert "Демо-профили" in about

    contacts = client.get("/contacts").get_data(as_text=True)
    assert "Оставить заявку" in contacts
    assert 'name="message"' in contacts


def test_no_placeholder_pages_left(client, demo):
    for path in PUBLIC_PAGES:
        html = client.get(path).get_data(as_text=True)
        assert "Раздел в разработке" not in html


def test_all_internal_links_resolve(client, demo):
    queue = list(PUBLIC_PAGES)
    seen = set()

    while queue:
        path = queue.pop()
        if path in seen:
            continue
        seen.add(path)

        response = client.get(path)
        assert response.status_code == 200, f"{path} -> {response.status_code}"

        html = response.get_data(as_text=True)
        for link in HREF_RE.findall(html):
            if link.startswith("/static/"):
                continue
            if link not in seen:
                queue.append(link)


def test_pages_have_single_h1_and_lang(client, demo):
    for path in PUBLIC_PAGES:
        html = client.get(path).get_data(as_text=True)
        assert 'lang="ru"' in html
        assert html.count("<h1") == 1, path
