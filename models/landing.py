from extensions import db


class LandingSettings(db.Model):
    __tablename__ = "landing_settings"

    id = db.Column(db.Integer, primary_key=True)
    resort_name = db.Column(db.String(120), nullable=False, default="Chaudhari's Resort")
    resort_address = db.Column(db.String(255), nullable=False, default="1 Coastal Road, Goa, India")
    hero_kicker = db.Column(db.String(120), nullable=False, default="A quieter kind of coastal escape")
    hero_title = db.Column(db.String(180), nullable=False,
                           default="Slow mornings. Salt air. Your own stretch of shore.")
    hero_description = db.Column(db.String(300), nullable=False,
                                 default="Thoughtful rooms, fresh-from-the-water dining, and the coast just beyond your door.")
    hero_image_url = db.Column(db.String(500), nullable=False,
                               default="https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=2200&q=88")
    intro_title = db.Column(db.String(120), nullable=False, default="A small resort that pays attention")
    intro_description = db.Column(db.Text, nullable=False,
                                  default="We keep the property small on purpose. Forty rooms, one pool, a beach that never feels crowded, and a team that remembers how you take your coffee.")
    intro_image_url = db.Column(db.String(500), nullable=False,
                                default="https://images.unsplash.com/photo-1518837695005-2083093ee35b?auto=format&fit=crop&w=1200&q=82")
    dining_title = db.Column(db.String(120), nullable=False, default="The restaurant")
    dining_description = db.Column(db.Text, nullable=False,
                                   default="Breakfast, lunch and dinner built around the day's catch and local produce, with a short menu that changes weekly.")
    dining_image_url = db.Column(db.String(500), nullable=False,
                                 default="https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=82")
    contact_title = db.Column(db.String(120), nullable=False, default="Talk to the front desk")
    contact_description = db.Column(db.String(300), nullable=False,
                                    default="Questions about a stay, a group booking or an event? We reply within a few hours.")
    phone = db.Column(db.String(40), nullable=False, default="+91 00000 00000")
    email = db.Column(db.String(150), nullable=False, default="stay@yourresort.example")


def get_landing_settings():
    settings = db.session.get(LandingSettings, 1)
    if settings is None:
        settings = LandingSettings(id=1)
        db.session.add(settings)
        db.session.commit()
    return settings