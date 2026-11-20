from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from app.extensions import db
from app.forms.public import LeadForm
from app.models import Lead, Project, Service, Testimonial

bp = Blueprint("public", __name__)

ABOUT_VALUES = [
    {
        "title": "Сначала задача",
        "text": (
            "Не начинаем с картинок. Сначала выясняем, какую задачу должен "
            "решать сайт и по каким признакам станет понятно, что он работает."
        ),
    },
    {
        "title": "Простота",
        "text": (
            "Убираем лишнее: чем меньше сущностей и настроек, тем проще "
            "поддерживать сайт и объяснять его команде."
        ),
    },
    {
        "title": "Прозрачность",
        "text": (
            "Показываем промежуточные результаты и честно говорим об "
            "ограничениях — по срокам, бюджету и объёму работ."
        ),
    },
]

ABOUT_TEAM = [
    {"name": "Алексей Морозов", "role": "Стратегия и исследования", "initials": "АМ"},
    {"name": "Марина Волкова", "role": "Дизайн-лид", "initials": "МВ"},
    {"name": "Павел Сидоров", "role": "Разработка", "initials": "ПС"},
    {"name": "Ольга Белова", "role": "Контент и брендинг", "initials": "ОБ"},
]


@bp.get("/")
def index():
    services = (
        Service.query.filter_by(is_published=True)
        .order_by(Service.sort_order, Service.id)
        .limit(4)
        .all()
    )
    projects = (
        Project.query.filter_by(is_published=True, is_featured=True)
        .order_by(Project.created_at.desc(), Project.id.desc())
        .limit(3)
        .all()
    )
    testimonials = (
        Testimonial.query.filter_by(is_published=True)
        .order_by(Testimonial.sort_order, Testimonial.id)
        .limit(3)
        .all()
    )
    return render_template(
        "public/index.html",
        services=services,
        projects=projects,
        testimonials=testimonials,
    )


@bp.get("/services")
def services():
    items = (
        Service.query.filter_by(is_published=True)
        .order_by(Service.sort_order, Service.id)
        .all()
    )
    return render_template("public/services.html", services=items)


@bp.get("/services/<slug>")
def service_detail(slug):
    service = Service.query.filter_by(slug=slug, is_published=True).first()
    if service is None:
        abort(404)

    other_services = (
        Service.query.filter(
            Service.is_published.is_(True),
            Service.id != service.id,
        )
        .order_by(Service.sort_order, Service.id)
        .limit(3)
        .all()
    )
    return render_template(
        "public/service_detail.html",
        service=service,
        other_services=other_services,
    )


@bp.get("/portfolio")
def portfolio():
    category = (request.args.get("category") or "").strip()

    categories = [
        row[0]
        for row in db.session.query(Project.category)
        .filter(Project.is_published.is_(True), Project.category != "")
        .distinct()
        .order_by(Project.category)
        .all()
    ]

    query = Project.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)

    projects = query.order_by(Project.created_at.desc(), Project.id.desc()).all()

    return render_template(
        "public/portfolio.html",
        projects=projects,
        categories=categories,
        active_category=category,
    )


@bp.get("/portfolio/<slug>")
def project_detail(slug):
    project = Project.query.filter_by(slug=slug, is_published=True).first()
    if project is None:
        abort(404)

    related = (
        Project.query.filter(
            Project.is_published.is_(True),
            Project.id != project.id,
        )
        .order_by(Project.created_at.desc(), Project.id.desc())
        .limit(3)
        .all()
    )
    return render_template(
        "public/project_detail.html",
        project=project,
        related=related,
    )


@bp.get("/about")
def about():
    return render_template(
        "public/about.html",
        values=ABOUT_VALUES,
        team=ABOUT_TEAM,
    )


@bp.route("/contacts", methods=["GET", "POST"])
def contacts():
    services = (
        Service.query.filter_by(is_published=True)
        .order_by(Service.sort_order, Service.id)
        .all()
    )

    form = LeadForm()
    form.service_id.choices = [(0, "Не выбрана")] + [
        (service.id, service.title) for service in services
    ]

    if request.method == "GET":
        slug = (request.args.get("service") or "").strip()
        selected = next((item for item in services if item.slug == slug), None)
        if selected is not None:
            form.service_id.data = selected.id

    if form.validate_on_submit():
        # Honeypot: бот заполнил скрытое поле — не сохраняем заявку.
        if form.website.data:
            return redirect(url_for("public.contacts_success"))

        lead = Lead(
            name=form.name.data,
            contact=form.contact.data,
            service_id=form.service_id.data or None,
            message=form.message.data,
        )
        db.session.add(lead)
        db.session.commit()
        flash("Заявка отправлена — мы свяжемся с вами.", "success")
        return redirect(url_for("public.contacts_success"))

    return render_template("public/contacts.html", form=form, services=services)


@bp.get("/contacts/success")
def contacts_success():
    return render_template("public/success.html")


@bp.get("/media/<path:filename>")
def media(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
