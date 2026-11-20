import click

from app.extensions import db
from app.models import AdminUser
from app.services.seed import seed_demo_data


def register_cli(app):
    @app.cli.command("init-db")
    def init_db_command():
        """Создать таблицы базы данных."""
        db.create_all()
        click.echo("База данных инициализирована.")

    @app.cli.command("seed")
    def seed_command():
        """Заполнить пустые таблицы демонстрационными данными."""
        created = seed_demo_data()
        click.echo(f"Добавлено записей: {created}.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin_command(username, password):
        """Создать администратора."""
        if AdminUser.query.filter_by(username=username).first() is not None:
            raise click.ClickException("Пользователь с таким именем уже существует.")

        user = AdminUser(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Администратор «{username}» создан.")

    @app.cli.command("set-password")
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def set_password_command(username, password):
        """Сменить пароль администратора."""
        user = AdminUser.query.filter_by(username=username).first()
        if user is None:
            raise click.ClickException("Пользователь не найден.")

        user.set_password(password)
        db.session.commit()
        click.echo(f"Пароль для «{username}» обновлён.")
