"""Сохранение и удаление изображений кейсов."""
from pathlib import Path
from uuid import uuid4

from flask import current_app

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def save_image(file_storage) -> str | None:
    """Сохраняет файл под случайным именем и возвращает его имя."""
    if file_storage is None or not file_storage.filename:
        return None

    filename = file_storage.filename
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = set(current_app.config.get("ALLOWED_IMAGE_EXTENSIONS") or ALLOWED_EXTENSIONS)
    if extension not in allowed:
        raise ValueError("Недопустимый формат файла.")

    name = f"{uuid4().hex}.{extension}"
    folder = Path(current_app.config["UPLOAD_FOLDER"])
    folder.mkdir(parents=True, exist_ok=True)
    file_storage.save(folder / name)
    return name


def delete_image(name: str | None) -> None:
    if not name:
        return

    path = Path(current_app.config["UPLOAD_FOLDER"]) / name
    if path.is_file():
        path.unlink()
