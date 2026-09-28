import os
import click
from flask import Flask, render_template
from config import Config
from extensions import db, bcrypt, csrf, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY is missing. Copy .env.example to .env and set it.")
    app.config["SESSION_COOKIE_SECURE"] = not app.debug and os.getenv("FLASK_ENV") == "production"

    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    import models  # noqa: F401  (registers tables)
    from models.landing import LandingSettings
    from routes import auth, main, rooms, bookings, housekeeping, staff, site
    for m in (auth, main, rooms, bookings, housekeeping, staff, site):
        app.register_blueprint(m.bp)

    for code, tpl in ((403, "403"), (404, "404"), (500, "500")):
        app.register_error_handler(code, lambda e, t=tpl, c=code: (render_template(f"errors/{t}.html"), c))

    @app.context_processor
    def inject():
        from models.landing import get_landing_settings
        settings = get_landing_settings()
        return {"resort_name": settings.resort_name, "resort_address": settings.resort_address}

    @app.cli.command("check-db")
    def check_db():
        """Verify the MySQL connection from your .env settings."""
        from sqlalchemy import text
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as e:
            raise click.ClickException(f"Cannot connect ({e.__class__.__name__}). Check .env values and that MySQL is running.")
        click.echo("Connected: " + db.engine.url.render_as_string(hide_password=True))

    @app.cli.command("seed-rooms")
    def seed_rooms():
        """Add sample rooms so the landing page has something to show."""
        from models.room import Room
        if Room.query.count():
            return click.echo("Rooms already exist; nothing added.")
        rows = [("101", "Standard", 1, 2, 2800, "WiFi,AC,TV"), ("102", "Deluxe", 1, 3, 4200, "WiFi,AC,TV,Balcony,Breakfast"),
                ("201", "Premium", 2, 3, 6100, "WiFi,AC,TV,Mini Bar,Balcony,Room Service"),
                ("202", "Suite", 2, 4, 9500, "WiFi,AC,TV,Mini Bar,Swimming Pool Access,Breakfast"),
                ("C1", "Cottage", 0, 4, 7800, "WiFi,AC,Parking,Balcony,Breakfast"),
                ("V1", "Villa", 0, 6, 16500, "WiFi,AC,TV,Swimming Pool Access,Parking,Room Service,Mini Bar")]
        for n, t, f, c, p, a in rows:
            db.session.add(Room(number=n, room_type=t, floor=f, capacity=c, price=p, amenities=a,
                                description=f"{t} room with sea-side views."))
        db.session.commit()
        click.echo("Sample rooms added.")

    @app.cli.command("init-db")
    def init_db():
        """Create all tables."""
        db.create_all()
        settings = db.session.get(LandingSettings, 1)
        if settings is None:
            settings = LandingSettings(resort_name=app.config["RESORT_NAME"],
                                      resort_address=app.config["RESORT_ADDRESS"])
            db.session.add(settings)
            db.session.commit()
        click.echo("Tables created.")

    @app.cli.command("create-admin")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.password_option()
    def create_admin(name, email, password):
        """Create the first Super Admin (password is validated and bcrypt-hashed)."""
        from models.user import User, Role
        from forms import strong_password
        from wtforms.validators import ValidationError

        class F:  # minimal stand-in so we reuse the same password rule
            data = password
        try:
            strong_password(None, F)
        except ValidationError as e:
            raise click.ClickException(str(e))
        if User.query.filter_by(email=email.lower()).first():
            raise click.ClickException("That email already exists.")
        u = User(name=name, email=email.lower(), role=Role.SUPER_ADMIN)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        click.echo(f"Super Admin {email} created.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
