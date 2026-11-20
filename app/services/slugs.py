"""Транслитерация и уникализация slug."""
import re

from sqlalchemy import select

from app.extensions import db

_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "і": "i", "ї": "yi", "є": "ye", "ґ": "g",
}


def slugify(value: str, max_length: int = 120) -> str:
    """Приводит строку к виду «latin-lower-case»."""
    value = (value or "").strip().lower()
    value = "".join(_TRANSLIT.get(char, char) for char in value)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if len(value) > max_length:
        value = value[:max_length].rstrip("-")
    return value or "item"


def unique_slug(model, value: str, exclude_id: int | None = None) -> str:
    """Возвращает slug, свободный для указанной модели."""
    base = slugify(value)
    slug = base
    counter = 2

    while True:
        stmt = select(model.id).where(model.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(model.id != exclude_id)
        if db.session.execute(stmt).first() is None:
            return slug
        slug = f"{base}-{counter}"
        counter += 1
