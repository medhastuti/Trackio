from flask import Flask, render_template, request, redirect
import sqlite3
from faker import Faker
import random
import os

app = Flask(__name__)
fake = Faker()

def connect_db():
    return sqlite3.connect("database.db")

# ------------------ RUN SQL FILE ------------------
def setup_database():
    conn = connect_db()
    cur = conn.cursor()

    with open("schema.sql", "r") as f:
        cur.executescript(f.read())

    # check if already seeded
    cur.execute("SELECT COUNT(*) FROM complaints")
    count = cur.fetchone()[0]

    if count == 0:

        issues = [
            "internet outage", "water leakage", "electric fault", "AC failure",
            "billing error", "login issue", "payment failure", "network slow",
            "lift malfunction", "garbage issue", "parking conflict", "noise disturbance"
        ]

        locations = [
            "in building A", "in flat 302", "near main gate", "in office area",
            "on 3rd floor", "in parking lot", "in server room", "in block C"
        ]

        statuses = ["Pending", "In Progress", "Resolved"]

        used_titles = set()

        for i in range(1, 5001):

            # 🔥 generate unique title
            while True:
                title = f"{random.choice(issues)} {random.choice(locations)} #{i}"
                if title not in used_titles:
                    used_titles.add(title)
                    break

            # 🔥 real description (long + meaningful)
            desc = fake.paragraph(nb_sentences=4)

            status = random.choice(statuses)

            # 🔥 feedback only for resolved
            if status == "Resolved":
                rating = random.randint(3, 5)
                feedback = fake.sentence(nb_words=10)
            else:
                rating = None
                feedback = None

            cur.execute("""
                INSERT INTO complaints (title, description, status, rating, feedback)
                VALUES (?, ?, ?, ?, ?)
            """, (title, desc, status, rating, feedback))

        # users
        cur.execute("INSERT INTO users VALUES (1,'User','user@gmail.com','123','user')")
        cur.execute("INSERT INTO users VALUES (2,'Admin','admin@gmail.com','123','admin')")
        cur.execute("INSERT INTO users VALUES (3,'Staff','staff@gmail.com','123','staff')")

    conn.commit()
    conn.close()

# ------------------ LOGIN ------------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email,password))
        user = cur.fetchone()
        conn.close()

        if user:
            role = user[4]
            if role == "admin":
                return redirect("/admin")
            elif role == "staff":
                return redirect("/staff")
            else:
                return redirect("/user")

    return render_template("login.html")

# ------------------ USER ------------------
@app.route("/user", methods=["GET","POST"])
def user():
    conn = connect_db()
    cur = conn.cursor()

    if request.method == "POST":
        # detect feedback vs new complaint
        if "feedback" in request.form:
            id = request.form["id"]
            rating = request.form["rating"]
            feedback = request.form["feedback"]

            cur.execute(
                "UPDATE complaints SET rating=?, feedback=? WHERE id=?",
                (rating, feedback, id)
            )
            conn.commit()
            conn.close()
            return redirect("/user")

        else:
            # normal complaint
            title = request.form["title"]
            desc = request.form["desc"]

            # 🔥 get next id
            cur.execute("SELECT MAX(id) FROM complaints")
            last_id = cur.fetchone()[0]

            next_id = (last_id or 0) + 1

            # append #number
            new_title = f"{title} #{next_id}"

            cur.execute(
                "INSERT INTO complaints (title, description, status) VALUES (?, ?, ?)",
                (new_title, desc, "Pending")
            )
            conn.commit()
            conn.close()
            return redirect("/user")

    # GET
    search = request.args.get("search")
    status = request.args.get("status")

    if search:
        cur.execute("SELECT * FROM complaints WHERE title LIKE ? ORDER BY id DESC LIMIT 20", (f"%{search}%",))
    elif status:
        cur.execute("SELECT * FROM complaints WHERE status=? ORDER BY id DESC LIMIT 20", (status,))
    else:
        cur.execute("SELECT * FROM complaints ORDER BY id DESC LIMIT 20")

    data = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM complaints")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'")
    pending = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'")
    resolved = cur.fetchone()[0]

    conn.close()

    return render_template("user.html", data=data, total=total, pending=pending, resolved=resolved)

# ------------------ ADMIN ------------------
@app.route("/admin", methods=["GET"])
def admin():
    conn = connect_db()
    cur = conn.cursor()

    search = request.args.get("search")
    status = request.args.get("status")

    if search:
        cur.execute("SELECT * FROM complaints WHERE title LIKE ? ORDER BY id DESC LIMIT 20", (f"%{search}%",))
    elif status:
        cur.execute("SELECT * FROM complaints WHERE status=? ORDER BY id DESC LIMIT 20", (status,))
    else:
        cur.execute("SELECT * FROM complaints ORDER BY id DESC LIMIT 20")

    data = cur.fetchall()
    
    cur.execute("SELECT COUNT(*) FROM complaints")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'")
    pending = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'")
    resolved = cur.fetchone()[0]

    conn.close()

    return render_template("admin.html", data=data, total=total, pending=pending, resolved=resolved)

# ------------------ STAFF ------------------
@app.route("/staff", methods=["GET","POST"])
def staff():
    conn = connect_db()
    cur = conn.cursor()

    if request.method == "POST":
        id = request.form["id"]
        cur.execute("UPDATE complaints SET status='Resolved' WHERE id=?", (id,))
        conn.commit()
        conn.close()
        return redirect("/staff")

    search = request.args.get("search")

    if search:
        cur.execute(
            "SELECT * FROM complaints WHERE status!='Resolved' AND title LIKE ? ORDER BY id DESC",
            ('%' + search + '%',)
        )
    else:
        cur.execute("SELECT * FROM complaints WHERE status!='Resolved' ORDER BY id DESC LIMIT 50")

    data = cur.fetchall()
    conn.close()

    return render_template("staff.html", data=data)

@app.route("/update_status", methods=["POST"])
def update_status():
    id = request.form["id"]
    status = request.form["status"]

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("UPDATE complaints SET status=? WHERE id=?", (status, id))

    conn.commit()
    conn.close()

    return redirect("/admin")

# ------------------ RUN ------------------
if __name__ == "__main__":
    setup_database()
    app.run(debug=True)