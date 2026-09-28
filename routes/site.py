from flask import Blueprint, flash, redirect, render_template, url_for
from extensions import db
from decorators import admin_required
from forms import LandingSettingsForm
from models.landing import get_landing_settings
from services.log_service import log_activity

bp = Blueprint("site", __name__)
EDITABLE_FIELDS = (
    "resort_name", "resort_address", "hero_kicker", "hero_title", "hero_description", "hero_image_url",
    "intro_title", "intro_description", "intro_image_url", "dining_title", "dining_description",
    "dining_image_url", "contact_title", "contact_description", "phone", "email",
)


@bp.route("/admin/landing", methods=["GET", "POST"])
@admin_required
def edit_landing():
    settings = get_landing_settings()
    form = LandingSettingsForm(obj=settings)
    if form.validate_on_submit():
        for field in EDITABLE_FIELDS:
            value = getattr(form, field).data
            setattr(settings, field, value.strip())
        log_activity("landing_page_updated", "Public landing page content updated")
        db.session.commit()
        flash("Landing page updated.", "success")
        return redirect(url_for("site.edit_landing"))
    return render_template("admin/landing.html", form=form)