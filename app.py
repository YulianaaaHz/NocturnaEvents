from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# On Render, set DATA_DIR to a persistent disk mount if you use one.
# Otherwise the database works normally but local files can be reset on a new deploy.
DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
os.makedirs(DATA_DIR, exist_ok=True)
DB = os.path.join(DATA_DIR, "nocturna.db")

TEXT_KEYS = [
    "site_name", "logo_text", "tagline", "description",
    "nav_home", "nav_events", "nav_gallery", "nav_about", "nav_quote",
    "discord_button",
    "hero_eyebrow", "hero_title", "hero_tagline", "hero_description",
    "hero_button", "hero_discord",
    "events_eyebrow", "events_title", "events_link",
    "about_eyebrow", "about_title", "about_text", "about_button", "quote_line",
    "gallery_eyebrow", "gallery_title", "gallery_link", "gallery_empty",
    "quote_title", "quote_intro", "quote_button",
    "footer_text", "admin_title", "admin_subtitle",
]

DEFAULT_SETTINGS = {
    # General
    "site_name": "NOCTURNA EVENTS",
    "logo_text": "NOCTURNA",
    "tagline": "La noche comienza aquí.",
    "description": "Somos un grupo de personas que disfrutamos de la noche, la música y los buenos momentos dentro de GTAHUB.",

    # Navigation
    "nav_home": "Inicio",
    "nav_events": "Eventos",
    "nav_gallery": "Galería",
    "nav_about": "Nosotros",
    "nav_quote": "Cotización",
    "discord_button": "DISCORD",
    "discord_url": "https://discord.gg/tu-servidor",

    # Design
    "primary_color": "#9b6cff",
    "secondary_color": "#161126",
    "hero_image": "",

    # Home / hero
    "hero_eyebrow": "GTAHUB • COMMUNITY • EVENTS",
    "hero_title": "NOCTURNA EVENTS",
    "hero_tagline": "La noche comienza aquí.",
    "hero_description": "Creamos experiencias, fiestas y eventos inolvidables dentro de GTAHUB.",
    "hero_button": "VER EVENTOS",
    "hero_discord": "DISCORD",
    # Position of the whole hero text block. Percentages are viewport-relative.
    "hero_text_x": "8",
    "hero_text_y": "50",
    "hero_text_align": "left",
    "hero_text_width": "750",
    "hero_text_scale": "100",

    # Home sections
    "events_eyebrow": "NOCTURNA",
    "events_title": "Eventos destacados",
    "events_link": "Ver todos →",
    "about_eyebrow": "NOCTURNA EVENTS",
    "about_title": "La noche se vive diferente.",
    "about_text": "Creamos fiestas, eventos y privados dentro de GTAHUB para disfrutar, bailar y compartir con la comunidad.",
    "about_button": "SOLICITAR COTIZACIÓN",
    "quote_line": "Música. Comunidad. Noches inolvidables.",
    "gallery_eyebrow": "NOCTURNA MOMENTS",
    "gallery_title": "Galería",
    "gallery_link": "Ver galería →",
    "gallery_empty": "Aún no hay fotografías.",

    # Quote
    "quote_title": "Haz realidad tu evento.",
    "quote_intro": "Cuéntanos qué tienes en mente y nuestro equipo preparará una propuesta para ti.",
    "quote_button": "SOLICITAR COTIZACIÓN",

    # Footer / admin
    "footer_text": "© 2026 NOCTURNA EVENTS • La noche se vive diferente.",
    "admin_title": "Panel de administración",
    "admin_subtitle": "Administra textos, diseño, eventos, álbumes y cotizaciones.",
    # Admin-only labels
    "save": "GUARDAR CAMBIOS",
    "new_event": "PUBLICAR EVENTO",
    "add_gallery": "AGREGAR FOTOS",
    "status_pending": "Pendiente",
    "status_review": "En revisión",
    "status_accepted": "Aceptada",
    "status_rejected": "Rechazada",
}

def db():
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT,
            time TEXT,
            location TEXT,
            description TEXT,
            image TEXT,
            category TEXT DEFAULT 'EVENTO',
            featured INTEGER DEFAULT 0
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            image TEXT NOT NULL,
            section TEXT DEFAULT 'Nocturna Moments'
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            event_type TEXT,
            event_date TEXT,
            event_time TEXT,
            people TEXT,
            location TEXT,
            budget TEXT,
            contact TEXT,
            details TEXT,
            status TEXT DEFAULT 'Pendiente'
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY CHECK(id=1),
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Safe migration: adds missing settings without overwriting anything
    # the owner has already customized.
    for key, value in DEFAULT_SETTINGS.items():
        con.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
            (key, value)
        )

    if not con.execute("SELECT id FROM admin WHERE id=1").fetchone():
        con.execute(
            "INSERT INTO admin(id, username, password) VALUES (1, ?, ?)",
            ("admin", "cambia-esta-clave")
        )

    con.commit()
    con.close()

def settings():
    con = db()
    rows = con.execute("SELECT key, value FROM settings").fetchall()
    con.close()
    data = dict(DEFAULT_SETTINGS)
    data.update({r["key"]: r["value"] for r in rows})
    return data

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

@app.context_processor
def inject():
    return {"site": settings()}

@app.route("/")
def index():
    con = db()
    events = con.execute(
        "SELECT * FROM events ORDER BY featured DESC, id DESC LIMIT 6"
    ).fetchall()
    # The database keeps every photo. The home page only previews the latest 8;
    # /galeria always shows every saved photo grouped by fiesta.
    gallery = con.execute(
        "SELECT * FROM gallery ORDER BY id DESC LIMIT 8"
    ).fetchall()
    con.close()
    return render_template("index.html", events=events, gallery=gallery)

@app.route("/eventos")
def eventos():
    con = db()
    events = con.execute(
        "SELECT * FROM events ORDER BY featured DESC, id DESC"
    ).fetchall()
    con.close()
    return render_template("events.html", events=events)

@app.route("/evento/<int:event_id>")
def evento(event_id):
    con = db()
    event = con.execute(
        "SELECT * FROM events WHERE id=?", (event_id,)
    ).fetchone()
    con.close()
    if not event:
        return "Evento no encontrado", 404
    return render_template("event.html", event=event)

@app.route("/galeria")
def galeria():
    con = db()
    gallery = con.execute(
        "SELECT * FROM gallery ORDER BY section COLLATE NOCASE ASC, id DESC"
    ).fetchall()
    con.close()

    groups = {}
    for item in gallery:
        groups.setdefault(item["section"] or "Nocturna Moments", []).append(item)

    return render_template("gallery.html", groups=groups)

@app.route("/nosotros")
def nosotros():
    return render_template("about.html")

@app.route("/cotizacion", methods=["GET", "POST"])
def cotizacion():
    if request.method == "POST":
        fields = [
            "name", "event_type", "event_date", "event_time", "people",
            "location", "budget", "contact", "details"
        ]
        values = tuple(request.form.get(k, "").strip() for k in fields)
        con = db()
        con.execute(
            """INSERT INTO quotes
            (name,event_type,event_date,event_time,people,location,budget,contact,details)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            values
        )
        con.commit()
        con.close()
        flash("Tu solicitud fue enviada correctamente.")
        return redirect(url_for("cotizacion"))
    return render_template("quote.html")

@app.route("/admin/gallery/bulk", methods=["POST"])
@admin_required
def gallery_bulk():
    section = request.form.get("section", "").strip() or "Nocturna Moments"
    title = request.form.get("title", "").strip()
    urls = [
        line.strip()
        for line in request.form.get("images", "").splitlines()
        if line.strip()
    ]

    if not urls:
        flash("No se agregó ninguna imagen. Pega al menos una URL por línea.")
        return redirect(url_for("admin", _anchor="gallery"))

    con = db()
    # INSERT only. Nothing is replaced or deleted when a new album is added.
    con.executemany(
        "INSERT INTO gallery(title, image, section) VALUES(?,?,?)",
        [(title, image_url, section) for image_url in urls]
    )
    con.commit()
    con.close()

    flash(f"{len(urls)} fotos agregadas a «{section}». Las anteriores se conservaron.")
    return redirect(url_for("admin", _anchor="gallery"))

@app.route("/admin/quote/<int:i>/status", methods=["POST"])
@admin_required
def quote_status(i):
    status = request.form.get("status", "").strip()
    allowed = {
        settings()["status_pending"],
        settings()["status_review"],
        settings()["status_accepted"],
        settings()["status_rejected"],
    }
    if status not in allowed:
        status = settings()["status_pending"]

    con = db()
    con.execute("UPDATE quotes SET status=? WHERE id=?", (status, i))
    con.commit()
    con.close()
    return redirect(url_for("admin", _anchor="quotes"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password_value = request.form.get("password", "")
        con = db()
        admin = con.execute(
            "SELECT * FROM admin WHERE id=1"
        ).fetchone()
        con.close()

        if admin and username == admin["username"] and password_value == admin["password"]:
            session["admin"] = True
            return redirect(url_for("admin"))

        flash("Usuario o contraseña incorrectos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin():
    con = db()
    events = con.execute("SELECT * FROM events ORDER BY featured DESC, id DESC").fetchall()
    gallery = con.execute(
        "SELECT * FROM gallery ORDER BY section COLLATE NOCASE ASC, id DESC"
    ).fetchall()
    quotes = con.execute("SELECT * FROM quotes ORDER BY id DESC").fetchall()
    con.close()
    return render_template("admin.html", events=events, gallery=gallery, quotes=quotes)

@app.route("/admin/settings", methods=["POST"])
@admin_required
def save_settings():
    con = db()

    # Only update keys that exist in the form and in our known settings.
    for key in DEFAULT_SETTINGS:
        if key in request.form:
            value = request.form.get(key, "").strip()

            # Clamp the position/size controls so a typo cannot break the layout.
            if key in {"hero_text_x", "hero_text_y"}:
                try:
                    value = str(max(0, min(100, float(value))))
                    if value.endswith(".0"):
                        value = value[:-2]
                except ValueError:
                    value = DEFAULT_SETTINGS[key]

            if key == "hero_text_width":
                try:
                    value = str(max(280, min(1200, int(float(value)))))
                except ValueError:
                    value = DEFAULT_SETTINGS[key]

            if key == "hero_text_scale":
                try:
                    value = str(max(70, min(140, int(float(value)))))
                except ValueError:
                    value = DEFAULT_SETTINGS[key]

            if key == "hero_text_align" and value not in {"left", "center", "right"}:
                value = "left"

            con.execute(
                "UPDATE settings SET value=? WHERE key=?",
                (value, key)
            )

    con.commit()
    con.close()
    flash("Configuración guardada.")
    return redirect(url_for("admin", _anchor="general"))

@app.route("/admin/event/new", methods=["POST"])
@admin_required
def new_event():
    con = db()
    con.execute(
        """INSERT INTO events
        (title,date,time,location,description,image,category,featured)
        VALUES(?,?,?,?,?,?,?,?)""",
        (
            request.form.get("title", "").strip(),
            request.form.get("date", "").strip(),
            request.form.get("time", "").strip(),
            request.form.get("location", "").strip(),
            request.form.get("description", "").strip(),
            request.form.get("image", "").strip(),
            request.form.get("category", "EVENTO").strip() or "EVENTO",
            1 if request.form.get("featured") else 0,
        )
    )
    con.commit()
    con.close()
    flash("Evento publicado.")
    return redirect(url_for("admin", _anchor="events"))

@app.route("/admin/event/delete/<int:event_id>", methods=["POST"])
@admin_required
def delete_event(event_id):
    con = db()
    con.execute("DELETE FROM events WHERE id=?", (event_id,))
    con.commit()
    con.close()
    flash("Evento eliminado.")
    return redirect(url_for("admin", _anchor="events"))

# Compatibility aliases for older templates/links.
@app.post("/admin/event/del/<int:i>")
@admin_required
def del_event(i):
    return delete_event(i)

@app.route("/admin/gallery/new", methods=["POST"])
@admin_required
def new_gallery():
    image = request.form.get("image", "").strip()
    title = request.form.get("title", "").strip()
    section = request.form.get("section", "").strip() or "Nocturna Moments"
    if image:
        con = db()
        con.execute(
            "INSERT INTO gallery(title,image,section) VALUES(?,?,?)",
            (title, image, section)
        )
        con.commit()
        con.close()
    return redirect(url_for("admin", _anchor="gallery"))

@app.route("/admin/gallery/delete/<int:item_id>", methods=["POST"])
@admin_required
def delete_gallery(item_id):
    con = db()
    con.execute("DELETE FROM gallery WHERE id=?", (item_id,))
    con.commit()
    con.close()
    flash("Foto eliminada. Las demás fotos se conservaron.")
    return redirect(url_for("admin", _anchor="gallery"))

@app.post("/admin/gallery/del/<int:i>")
@admin_required
def del_gallery(i):
    return delete_gallery(i)

@app.route("/admin/quote/delete/<int:i>", methods=["POST"])
@admin_required
def delete_quote(i):
    con = db()
    con.execute("DELETE FROM quotes WHERE id=?", (i,))
    con.commit()
    con.close()
    flash("Cotización eliminada.")
    return redirect(url_for("admin", _anchor="quotes"))

# Compatibility alias for the old template.
@app.post("/admin/quote/del/<int:i>")
@admin_required
def del_quote(i):
    return delete_quote(i)

@app.route("/admin/password", methods=["POST"])
@admin_required
def password():
    username = request.form.get("username", "").strip()
    password_value = request.form.get("password", "")
    if not username or not password_value:
        flash("El usuario y la contraseña no pueden estar vacíos.")
        return redirect(url_for("admin", _anchor="security"))

    con = db()
    con.execute(
        "UPDATE admin SET username=?, password=? WHERE id=1",
        (username, password_value)
    )
    con.commit()
    con.close()
    flash("Credenciales actualizadas.")
    return redirect(url_for("admin", _anchor="security"))

# Initialize/migrate before serving requests.
init_db()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False
    )
