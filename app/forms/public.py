from app.forms import strip_text

from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length


class LeadForm(FlaskForm):
    name = StringField(
        "Имя",
        filters=[strip_text],
        validators=[
            DataRequired(message="Укажите имя."),
            Length(min=2, max=120, message="Имя должно быть от 2 до 120 символов."),
        ],
        render_kw={"placeholder": "Как к вам обращаться", "autocomplete": "name"},
    )
    contact = StringField(
        "Контакт",
        filters=[strip_text],
        validators=[
            DataRequired(message="Оставьте телефон, email или Telegram."),
            Length(min=3, max=160, message="Контакт должен быть от 3 до 160 символов."),
        ],
        render_kw={"placeholder": "Телефон, email или @telegram"},
    )
    service_id = SelectField(
        "Услуга",
        coerce=int,
        default=0,
        validators=[],
    )
    message = TextAreaField(
        "Задача",
        filters=[strip_text],
        validators=[
            DataRequired(message="Опишите задачу."),
            Length(min=10, max=2000, message="Сообщение должно быть от 10 до 2000 символов."),
        ],
        render_kw={
            "rows": 6,
            "placeholder": "Коротко о задаче, сроках и бюджете",
        },
    )
    # Ловушка для спам-ботов: люди это поле не видят.
    website = HiddenField()
