from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os, secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
DB = os.path.join(os.path.dirname(__file__), "nocturna.db")

DEFAULT_SETTINGS = {
    "site_name": "NOCTURNA EVENTS",
    "tagline": "La noche comienza aquí.",
    "description": "Somos un grupo de personas que disfrutamos de la noche, la música y los buenos momentos dentro de GTAHUB. Organizamos fiestas, eventos y privados para crear experiencias diferentes.",
    "discord_url": "https://discord.gg/tu-servidor",
    "primary_color": "#8b5cf6",
    "secondary_color": "#11111b",
    "hero_image": "",
    "logo_text": "NOCTURNA",
    "footer_text": "NOCTURNA EVENTS • GTAHUB",
}

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, date TEXT, time TEXT, location TEXT,
        description TEXT, image TEXT, category TEXT DEFAULT 'EVENTO',
        featured INTEGER DEFAULT 0
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS gallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, image TEXT NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY CHECK(id=1),
        username TEXT NOT NULL, password TEXT NOT NULL
    )""")
    for k, v in DEFAULT_SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)", (k, v))
    if not con.execute("SELECT id FROM admin WHERE id=1").fetchone():
        con.execute("INSERT INTO admin(id,username,password) VALUES (1,?,?)", ("admin", "cambia-esta-clave"))
    con.commit()
    con.close()

def settings():
    con = db()
    rows = con.execute("SELECT key,value FROM settings").fetchall()
    con.close()
    return {r["key"]: r["value"] for r in rows}

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
    events = con.execute("SELECT * FROM events ORDER BY id DESC LIMIT 6").fetchall()
    gallery = con.execute("SELECT * FROM gallery ORDER BY id DESC LIMIT 8").fetchall()
    con.close()
    return render_template("index.html", events=events, gallery=gallery)

@app.route("/eventos")
def eventos():
    con = db()
    events = con.execute("SELECT * FROM events ORDER BY id DESC").fetchall()
    con.close()
    return render_template("events.html", events=events)

@app.route("/evento/<int:event_id>")
def evento(event_id):
    con = db()
    event = con.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    con.close()
    if not event:
        return "Evento no encontrado", 404
    return render_template("event.html", event=event)

@app.route("/galeria")
def galeria():
    con = db()
    gallery = con.execute("SELECT * FROM gallery ORDER BY id DESC").fetchall()
    con.close()
    return render_template("gallery.html", gallery=gallery)

@app.route("/nosotros")
def nosotros():
    return render_template("about.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        con = db()
        admin = con.execute("SELECT * FROM admin WHERE id=1").fetchone()
        con.close()
        if request.form["username"] == admin["username"] and request.form["password"] == admin["password"]:
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
    events = con.execute("SELECT * FROM events ORDER BY id DESC").fetchall()
    gallery = con.execute("SELECT * FROM gallery ORDER BY id DESC").fetchall()
    con.close()
    return render_template("admin.html", events=events, gallery=gallery)

@app.route("/admin/settings", methods=["POST"])
@admin_required
def save_settings():
    con = db()
    for key in DEFAULT_SETTINGS:
        if key in request.form:
            con.execute("UPDATE settings SET value=? WHERE key=?", (request.form[key], key))
    con.commit(); con.close()
    flash("Configuración guardada.")
    return redirect(url_for("admin"))

@app.route("/admin/event/new", methods=["POST"])
@admin_required
def new_event():
    con = db()
    con.execute("""INSERT INTO events(title,date,time,location,description,image,category,featured)
                   VALUES(?,?,?,?,?,?,?,?)""", (
        request.form["title"], request.form["date"], request.form["time"],
        request.form["location"], request.form["description"], request.form["image"],
        request.form["category"], 1 if request.form.get("featured") else 0))
    con.commit(); con.close()
    return redirect(url_for("admin"))

@app.route("/admin/event/delete/<int:event_id>", methods=["POST"])
@admin_required
def delete_event(event_id):
    con = db(); con.execute("DELETE FROM events WHERE id=?", (event_id,)); con.commit(); con.close()
    return redirect(url_for("admin"))

@app.route("/admin/gallery/new", methods=["POST"])
@admin_required
def new_gallery():
    con = db()
    con.execute("INSERT INTO gallery(title,image) VALUES(?,?)", (request.form["title"], request.form["image"]))
    con.commit(); con.close()
    return redirect(url_for("admin"))

@app.route("/admin/gallery/delete/<int:item_id>", methods=["POST"])
@admin_required
def delete_gallery(item_id):
    con = db(); con.execute("DELETE FROM gallery WHERE id=?", (item_id,)); con.commit(); con.close()
    return redirect(url_for("admin"))

@app.route("/admin/password", methods=["POST"])
@admin_required
def password():
    con = db()
    con.execute("UPDATE admin SET username=?, password=? WHERE id=1",
                (request.form["username"], request.form["password"]))
    con.commit(); con.close()
    flash("Credenciales actualizadas.")
    return redirect(url_for("admin"))

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
