from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app.extensions import db, login_manager
from app.forms.admin import (
    LeadStatusForm,
    LoginForm,
    ProjectForm,
    ServiceForm,
    TestimonialForm,
)
from app.models import AdminUser, Lead, Project, Service, Testimonial
from app.services.slugs import slugify, unique_slug
from app.services.uploads import delete_image, save_image

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
def protect_admin():
    if request.endpoint != "admin.login" and not current_user.is_authenticated:
        return login_manager.unauthorized()
    return None


def _apply_slug(form, model, instance) -> bool:
    """Проверяет ручной slug или генерирует уникальный автоматически."""
    raw = (form.slug.data or "").strip()
    exclude_id = instance.id if instance is not None else None

    if raw:
        candidate = slugify(raw)
        query = model.query.filter(model.slug == candidate)
        if exclude_id is not None:
            query = query.filter(model.id != exclude_id)
        if query.first() is not None:
            form.slug.errors.append("Такой slug уже используется.")
            return False
        form.slug.data = candidate
    else:
        form.slug.data = unique_slug(model, form.title.data, exclude_id)

    return True


def _commit_or_flash(success_message: str) -> bool:
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Не удалось сохранить: проверьте уникальность slug.", "danger")
        return False
    flash(success_message, "success")
    return True


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_url = request.args.get("next", "")
            if not next_url.startswith("/") or urlsplit(next_url).netloc:
                next_url = url_for("admin.dashboard")
            return redirect(next_url)
        flash("Неверный логин или пароль.", "danger")

    return render_template("admin/login.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из админки.", "success")
    return redirect(url_for("admin.login"))


@bp.get("/")
def dashboard():
    stats = {
        "services": Service.query.count(),
        "services_published": Service.query.filter_by(is_published=True).count(),
        "projects": Project.query.count(),
        "projects_published": Project.query.filter_by(is_published=True).count(),
        "testimonials": Testimonial.query.count(),
        "testimonials_published": Testimonial.query.filter_by(is_published=True).count(),
        "leads": Lead.query.count(),
        "leads_new": Lead.query.filter_by(status="new").count(),
    }
    recent_leads = (
        Lead.query.order_by(Lead.created_at.desc(), Lead.id.desc()).limit(5).all()
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_leads=recent_leads,
    )


# ---------- Услуги ----------


@bp.get("/services")
def services():
    items = Service.query.order_by(Service.sort_order, Service.id).all()
    return render_template("admin/services.html", services=items)


@bp.route("/services/new", methods=["GET", "POST"])
def service_new():
    form = ServiceForm()
    if form.validate_on_submit():
        service = Service()
        if not _apply_slug(form, Service, service):
            return render_template("admin/service_form.html", form=form, service=None)

        form.populate_obj(service)
        service.sort_order = service.sort_order or 0
        db.session.add(service)
        if _commit_or_flash("Услуга создана."):
            return redirect(url_for("admin.services"))
        return render_template("admin/service_form.html", form=form, service=None)

    return render_template("admin/service_form.html", form=form, service=None)


@bp.route("/services/<int:service_id>/edit", methods=["GET", "POST"])
def service_edit(service_id):
    service = db.get_or_404(Service, service_id)
    form = ServiceForm(obj=service)

    if form.validate_on_submit():
        if not _apply_slug(form, Service, service):
            return render_template("admin/service_form.html", form=form, service=service)

        form.populate_obj(service)
        service.sort_order = service.sort_order or 0
        if _commit_or_flash("Услуга обновлена."):
            return redirect(url_for("admin.services"))
        return render_template("admin/service_form.html", form=form, service=service)

    return render_template("admin/service_form.html", form=form, service=service)


@bp.post("/services/<int:service_id>/toggle")
def service_toggle(service_id):
    service = db.get_or_404(Service, service_id)
    service.is_published = not service.is_published
    db.session.commit()
    state = "опубликована" if service.is_published else "скрыта"
    flash(f"Услуга {state}.", "success")
    return redirect(url_for("admin.services"))


@bp.post("/services/<int:service_id>/delete")
def service_delete(service_id):
    service = db.get_or_404(Service, service_id)
    db.session.delete(service)
    db.session.commit()
    flash("Услуга удалена.", "success")
    return redirect(url_for("admin.services"))


# ---------- Кейсы ----------


@bp.get("/projects")
def projects():
    items = Project.query.order_by(Project.created_at.desc(), Project.id.desc()).all()
    return render_template("admin/projects.html", projects=items)


@bp.route("/projects/new", methods=["GET", "POST"])
def project_new():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project()
        if not _apply_slug(form, Project, project):
            return render_template("admin/project_form.html", form=form, project=None)

        new_image = None
        if form.image.data:
            try:
                new_image = save_image(form.image.data)
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("admin/project_form.html", form=form, project=None)

        form.populate_obj(project)
        project.image_path = new_image
        db.session.add(project)
        if _commit_or_flash("Кейс создан."):
            return redirect(url_for("admin.projects"))
        if new_image is not None:
            delete_image(new_image)
        return render_template("admin/project_form.html", form=form, project=None)

    return render_template("admin/project_form.html", form=form, project=None)


@bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
def project_edit(project_id):
    project = db.get_or_404(Project, project_id)
    form = ProjectForm(obj=project)

    if form.validate_on_submit():
        if not _apply_slug(form, Project, project):
            return render_template("admin/project_form.html", form=form, project=project)

        old_image = project.image_path
        new_image = None
        if form.image.data:
            try:
                new_image = save_image(form.image.data)
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("admin/project_form.html", form=form, project=project)

        form.populate_obj(project)
        if new_image is not None:
            project.image_path = new_image

        if _commit_or_flash("Кейс обновлён."):
            if new_image is not None and old_image:
                delete_image(old_image)
            return redirect(url_for("admin.projects"))
        if new_image is not None:
            delete_image(new_image)
        return render_template("admin/project_form.html", form=form, project=project)

    return render_template("admin/project_form.html", form=form, project=project)


@bp.post("/projects/<int:project_id>/toggle")
def project_toggle(project_id):
    project = db.get_or_404(Project, project_id)
    project.is_published = not project.is_published
    db.session.commit()
    state = "опубликован" if project.is_published else "скрыт"
    flash(f"Кейс {state}.", "success")
    return redirect(url_for("admin.projects"))


@bp.post("/projects/<int:project_id>/feature")
def project_feature(project_id):
    project = db.get_or_404(Project, project_id)
    project.is_featured = not project.is_featured
    db.session.commit()
    state = "добавлен в избранные" if project.is_featured else "убран из избранных"
    flash(f"Кейс {state}.", "success")
    return redirect(url_for("admin.projects"))


@bp.post("/projects/<int:project_id>/delete")
def project_delete(project_id):
    project = db.get_or_404(Project, project_id)
    image = project.image_path
    db.session.delete(project)
    db.session.commit()
    delete_image(image)
    flash("Кейс удалён.", "success")
    return redirect(url_for("admin.projects"))


# ---------- Отзывы ----------


@bp.get("/testimonials")
def testimonials():
    items = Testimonial.query.order_by(Testimonial.sort_order, Testimonial.id).all()
    return render_template("admin/testimonials.html", testimonials=items)


@bp.route("/testimonials/new", methods=["GET", "POST"])
def testimonial_new():
    form = TestimonialForm()
    if form.validate_on_submit():
        testimonial = Testimonial()
        form.populate_obj(testimonial)
        testimonial.sort_order = testimonial.sort_order or 0
        db.session.add(testimonial)
        if _commit_or_flash("Отзыв создан."):
            return redirect(url_for("admin.testimonials"))
        return render_template(
            "admin/testimonial_form.html", form=form, testimonial=None
        )

    return render_template("admin/testimonial_form.html", form=form, testimonial=None)


@bp.route("/testimonials/<int:testimonial_id>/edit", methods=["GET", "POST"])
def testimonial_edit(testimonial_id):
    testimonial = db.get_or_404(Testimonial, testimonial_id)
    form = TestimonialForm(obj=testimonial)

    if form.validate_on_submit():
        form.populate_obj(testimonial)
        testimonial.sort_order = testimonial.sort_order or 0
        if _commit_or_flash("Отзыв обновлён."):
            return redirect(url_for("admin.testimonials"))
        return render_template(
            "admin/testimonial_form.html", form=form, testimonial=testimonial
        )

    return render_template(
        "admin/testimonial_form.html", form=form, testimonial=testimonial
    )


@bp.post("/testimonials/<int:testimonial_id>/toggle")
def testimonial_toggle(testimonial_id):
    testimonial = db.get_or_404(Testimonial, testimonial_id)
    testimonial.is_published = not testimonial.is_published
    db.session.commit()
    state = "опубликован" if testimonial.is_published else "скрыт"
    flash(f"Отзыв {state}.", "success")
    return redirect(url_for("admin.testimonials"))


@bp.post("/testimonials/<int:testimonial_id>/delete")
def testimonial_delete(testimonial_id):
    testimonial = db.get_or_404(Testimonial, testimonial_id)
    db.session.delete(testimonial)
    db.session.commit()
    flash("Отзыв удалён.", "success")
    return redirect(url_for("admin.testimonials"))


# ---------- Заявки ----------


def _lead_statuses():
    return [
        (value, Lead.STATUS_LABELS[value])
        for value in Lead.STATUSES
    ]


@bp.get("/leads")
def leads():
    active_status = (request.args.get("status") or "").strip()
    query = Lead.query
    if active_status in Lead.STATUSES:
        query = query.filter_by(status=active_status)
    items = query.order_by(Lead.created_at.desc(), Lead.id.desc()).all()

    return render_template(
        "admin/leads.html",
        leads=items,
        statuses=_lead_statuses(),
        active_status=active_status,
        counts={
            status: Lead.query.filter_by(status=status).count()
            for status in Lead.STATUSES
        },
        total=Lead.query.count(),
    )


@bp.route("/leads/<int:lead_id>", methods=["GET", "POST"])
def lead_detail(lead_id):
    lead = db.get_or_404(Lead, lead_id)
    form = LeadStatusForm(obj=lead)
    form.status.choices = _lead_statuses()

    if form.validate_on_submit():
        lead.status = form.status.data
        db.session.commit()
        flash("Статус заявки обновлён.", "success")
        return redirect(url_for("admin.lead_detail", lead_id=lead.id))

    return render_template("admin/lead_detail.html", lead=lead, form=form)
