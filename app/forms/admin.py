from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileSize
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.forms import strip_text


class LoginForm(FlaskForm):
    username = StringField(
        "Логин",
        filters=[strip_text],
        validators=[DataRequired(message="Введите логин."), Length(max=80)],
        render_kw={"autocomplete": "username"},
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired(message="Введите пароль."), Length(max=255)],
        render_kw={"autocomplete": "current-password"},
    )
    remember = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class ServiceForm(FlaskForm):
    title = StringField(
        "Название",
        filters=[strip_text],
        validators=[DataRequired(message="Укажите название."), Length(max=120)],
    )
    slug = StringField(
        "Slug",
        filters=[strip_text],
        validators=[Optional(), Length(max=140)],
        render_kw={"placeholder": "Оставьте пустым для автогенерации"},
    )
    short_description = StringField(
        "Короткое описание",
        filters=[strip_text],
        validators=[Optional(), Length(max=300)],
    )
    description = TextAreaField(
        "Описание",
        filters=[strip_text],
        validators=[Optional(), Length(max=5000)],
        render_kw={"rows": 5},
    )
    icon_name = StringField(
        "Иконка",
        filters=[strip_text],
        validators=[Optional(), Length(max=50)],
    )
    is_published = BooleanField("Опубликовано", default=True)
    sort_order = IntegerField(
        "Порядок",
        default=0,
        validators=[Optional(), NumberRange(min=0, max=99999)],
    )
    submit = SubmitField("Сохранить")


class ProjectForm(FlaskForm):
    title = StringField(
        "Название",
        filters=[strip_text],
        validators=[DataRequired(message="Укажите название."), Length(max=160)],
    )
    slug = StringField(
        "Slug",
        filters=[strip_text],
        validators=[Optional(), Length(max=160)],
        render_kw={"placeholder": "Оставьте пустым для автогенерации"},
    )
    category = StringField(
        "Категория",
        filters=[strip_text],
        validators=[Optional(), Length(max=80)],
    )
    summary = StringField(
        "Краткое описание",
        filters=[strip_text],
        validators=[Optional(), Length(max=300)],
    )
    challenge = TextAreaField(
        "Задача",
        filters=[strip_text],
        validators=[Optional(), Length(max=5000)],
        render_kw={"rows": 4},
    )
    solution = TextAreaField(
        "Решение",
        filters=[strip_text],
        validators=[Optional(), Length(max=5000)],
        render_kw={"rows": 4},
    )
    outcome = TextAreaField(
        "Результат",
        filters=[strip_text],
        validators=[Optional(), Length(max=5000)],
        render_kw={"rows": 4},
    )
    image = FileField(
        "Обложка",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Только JPG, PNG или WebP."),
            FileSize(max_size=2 * 1024 * 1024, message="Файл больше 2 МБ."),
        ],
    )
    is_featured = BooleanField("Избранный кейс")
    is_published = BooleanField("Опубликовано", default=True)
    submit = SubmitField("Сохранить")


class TestimonialForm(FlaskForm):
    author_name = StringField(
        "Автор",
        filters=[strip_text],
        validators=[DataRequired(message="Укажите автора."), Length(max=120)],
    )
    company_label = StringField(
        "Компания",
        filters=[strip_text],
        validators=[Optional(), Length(max=120)],
    )
    text = TextAreaField(
        "Текст отзыва",
        filters=[strip_text],
        validators=[
            DataRequired(message="Введите текст отзыва."),
            Length(min=10, max=2000, message="Текст должен быть от 10 до 2000 символов."),
        ],
        render_kw={"rows": 5},
    )
    is_published = BooleanField("Опубликован", default=True)
    sort_order = IntegerField(
        "Порядок",
        default=0,
        validators=[Optional(), NumberRange(min=0, max=99999)],
    )
    submit = SubmitField("Сохранить")


class LeadStatusForm(FlaskForm):
    status = SelectField("Статус", validators=[DataRequired()])
    submit = SubmitField("Обновить статус")
