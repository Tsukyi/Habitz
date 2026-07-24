from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import secrets
import time
import datetime

def generate_secure_token():
    return secrets.token_hex(32)  # this is a generated 64-char token

# Configure application
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

DATABASE = "habit.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
@app.route("/")

def index():
    if "user_id" not in session:
        return redirect("/login")
    return redirect("/dashboard")

def render_error(template, message, **kwargs):
    """Render a template with an error message."""
    return render_template(template, error_message=message, **kwargs)

def render_success(template, message, **kwargs):
    """Render a template with a success message."""
    return render_template(template, success_message=message, **kwargs)

def update_habit_streak(conn, habit_id):
    habit = conn.execute(
        "SELECT current_streak, longest_streak, last_completed_date FROM habits WHERE id = ?",
        (habit_id,)
    ).fetchone()

    if habit is None:
        return

    today = datetime.datetime.utcnow().date()

    if habit["last_completed_date"]:
        last_date = datetime.strptime(
            habit["last_completed_date"], "%Y-%m-%d"
        ).date()
    else:
        last_date = None

    # Already completed today
    if last_date == today:
        return

    if last_date == today - datetime.timedelta(days=1):
        new_streak = habit["current_streak"] + 1
    else:
        new_streak = 1

    new_longest = max(new_streak, habit["longest_streak"])

    conn.execute(
        """
        UPDATE habits
        SET current_streak = ?, longest_streak = ?, last_completed_date = ?
        WHERE id = ?
        """,
        (new_streak, new_longest, today, habit_id)
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_error("login.html", "Must provide username and password")

        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchall()

        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], password):
            return render_error("login.html", "Invalid username and/or password")

        session["user_id"] = rows[0]["id"]

        # NEW: unlock music after login
        session["music_allowed"] = True

        record_login(session["user_id"])
        today = datetime.datetime.today().isoformat()
        record_login(session["user_id"])
        today = datetime.datetime.today().isoformat()

        # Check if already logged today
        existing = conn.execute(
            "SELECT 1 FROM login_activity WHERE user_id = ? AND login_date = ?",
            (session["user_id"], today)
        ).fetchone()

        if not existing:
            conn.execute(
                "INSERT INTO login_activity (user_id, login_date) VALUES (?, ?)",
                (session["user_id"], today)
            )
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        key = request.form.get("key")

        if not username:
            flash("must provide username")
            return redirect("/register")

        if not password:
            flash("must provide password")
            return redirect("/register")

        if password != confirmation:
            flash("passwords are mismatched")
            return redirect("/register")

        conn = get_db()

        rows = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchall()

        if rows:
            conn.close()
            flash("username already exists")
            return redirect("/register")

        hashed_password = generate_password_hash(password)

        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hashed_password)
        )

        conn.commit()

        session["user_id"] = cursor.lastrowid

        conn.close()

        return redirect("/")

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    user = conn.execute(
        "SELECT username FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    tasks = conn.execute(
        "SELECT * FROM habits WHERE user_id = ? AND completed = 0 ORDER BY end_date",
        (session["user_id"],)
    ).fetchall()

    completed = conn.execute(
        """
        SELECT completions.habit_name, completions.date_completed,
            habits.end_date
        FROM completions
        LEFT JOIN habits ON habits.id = completions.habit_id
        WHERE completions.user_id = ?
        ORDER BY completions.date_completed DESC

        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template("dashboard.html",user=user,tasks=tasks,completed=completed)

@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if request.method == "POST":

        if "user_id" not in session:
            return redirect("/login")

        description = request.form.get("description")
        task = request.form.get("task")
        start_date = request.form.get("startdate")
        end_date = request.form.get("enddate")
        days = request.form.get("days")
        if not task:
            return render_error("tasks.html", "Must provide a task")

        conn = get_db()
        conn.execute(
            "INSERT INTO habits (user_id, name, start_date, end_date, duration, description) VALUES (?, ?, ?, ?, ?, ?)",
            (session["user_id"], task, start_date, end_date, days, description)
        )
        conn.commit()
        conn.close()

        return render_success("tasks.html", "Task added successfully")

    return render_template("tasks.html")

@app.route("/reset", methods=["GET", "POST"])
def reset():
    if request.method == "POST":
        username = request.form.get("username")

        if not username:
            return render_error("reset.html", "Must provide username")

        conn = get_db()
        user = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if not user:
            conn.close()
            return render_error("reset.html", "User not found")

        token = generate_secure_token()
        expires_at = int(time.time()) + 600  # 10 minutes

        conn.execute(
            "INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user["id"], token, expires_at)
        )
        conn.commit()
        conn.close()

        public_url = "https://automatic-goggles-97654p9j7jr437xg-5000.app.github.dev"
        reset_link = f"{public_url}/reset/{token}"
        print("Password reset link:", reset_link)

        return render_success("login.html", "Reset link generated (check link @ console)")

    return render_template("reset.html")

@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_with_token(token):
    conn = get_db()

    record = conn.execute(
        "SELECT * FROM password_resets WHERE token = ?",
        (token,)
    ).fetchone()

    if not record:
        conn.close()
        return "Invalid or expired token"

    if record["used"] == 1:
        conn.close()
        return "Token already used"

    if record["expires_at"] < int(time.time()):
        conn.close()
        return "Token expired"

    if request.method == "POST":
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not password or password != confirmation:
            conn.close()
            return render_error("password.html", "Passwords do not match")

        hashed_password = generate_password_hash(password)

        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hashed_password, record["user_id"])
        )

        # Mark token as used
        conn.execute(
            "UPDATE password_resets SET used = 1 WHERE id = ?",
            (record["id"],)
        )

        conn.commit()
        conn.close()

        return render_success("login.html", "Password reset successful")

    conn.close()
    return render_template("password.html")

@app.route("/overview", methods=["GET", "POST"])
def overview():
    if "user_id" not in session:
        return redirect("/login")

    sort = request.args.get("sort", "favorite")
    conn = get_db()

    if request.method == "POST":
        done = request.form.get("done")
        print("DONE TASK ID:", done)

        if done:
            done = int(done)
            habit = conn.execute(
                "SELECT name FROM habits WHERE id = ?",
                (done,)
            ).fetchone()

            conn.execute(
                "INSERT OR IGNORE INTO completions (habit_id, user_id, habit_name, date_completed, completed) VALUES (?, ?, ?, ?, 1)",
                (done, session["user_id"], habit["name"], datetime.date.today().isoformat())
            )
            update_habit_streak(conn, done)

            conn.execute(
                "UPDATE habits SET completed = 1 WHERE id = ? AND user_id = ?",
                (done, session["user_id"])
            )

            conn.commit()

        return redirect("/overview")

    order_by = "favorite DESC, start_date ASC"
    if sort in ["start_asc", "start_desc"]:
        order_by = f"favorite DESC, start_date {'ASC' if sort=='start_asc' else 'DESC'}"
    elif sort in ["end_asc", "end_desc"]:
        order_by = f"favorite DESC, end_date {'ASC' if sort=='end_asc' else 'DESC'}"
    elif sort in ["alpha_asc", "alpha_desc"]:
        order_by = f"favorite DESC, name {'ASC' if sort=='alpha_asc' else 'DESC'}"

    cursor = conn.execute(
        f"SELECT * FROM habits WHERE user_id = ? AND completed = 0 ORDER BY {order_by}",
        (session["user_id"],)
    )

    tasks = cursor.fetchall()

    task_list = []

    for task in tasks:
        task_dict = dict(task)

        end_date = datetime.datetime.strptime(task_dict["end_date"], "%Y-%m-%d").date()
        today = datetime.date.today()
        remaining_days = (end_date - today).days

        # Prevent negative values
        task_dict["days_left"] = max(remaining_days, 0)

        task_list.append(task_dict)

    # Count total completed tasks
    completed_count = conn.execute(
        "SELECT COUNT(*) FROM completions WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()[0]

    conn.close()

    return render_template(
        "overview.html",
        tasks=task_list,
        current_sort=sort,
        completed_count=completed_count
    )

@app.route("/overview/favorite", methods=["POST"])
def favorite_task():
    if "user_id" not in session:
        return "", 403

    task_id = request.form.get("task_id")
    if not task_id:
        return "", 400

    conn = get_db()
    # Toggle favorite: if 1 → 0, if 0 → 1
    conn.execute(
        """
        UPDATE habits
        SET favorite = CASE WHEN favorite = 1 THEN 0 ELSE 1 END
        WHERE id = ? AND user_id = ?
        """,
        (task_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return "", 204


@app.route("/calendar")
def calendar():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    rows = conn.execute(
        "SELECT login_date FROM login_activity WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    login_count = conn.execute(
        "SELECT current_streak FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()["current_streak"]

    conn.close()

    login_dates = {row["login_date"] for row in rows}

    days = [(datetime.datetime.utcnow().date() - datetime.timedelta(days=i)).isoformat() for i in range(30)]

    return render_template("calendar.html", login_dates=login_dates, days=days, login_count=login_count)

def record_login(user_id):
    """Record a login and update streak safely using server date."""
    conn = get_db()
    today = datetime.datetime.utcnow().date()

    user = conn.execute(
        "SELECT current_streak, longest_streak, last_login_date FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    if user["last_login_date"]:
        last_login = datetime.datetime.strptime(user["last_login_date"], "%Y-%m-%d").date()
    else:
        last_login = None

    # Ignore future logins (someone changed system clock)
    if last_login and last_login > today:
        conn.close()
        return

    # Already logged in today → do nothing
    if last_login == today:
        conn.close()
        return

    # Update streak
    if last_login == today - datetime.timedelta(days=1):
        new_streak = user["current_streak"] + 1
    else:
        new_streak = 1

    new_longest = max(new_streak, user["longest_streak"])

    # Update streak in users table
    conn.execute(
        "UPDATE users SET current_streak=?, longest_streak=?, last_login_date=? WHERE id=?",
        (new_streak, new_longest, today, user_id)
    )

    # Insert today’s login into login_activity if not already present
    existing = conn.execute(
        "SELECT 1 FROM login_activity WHERE user_id=? AND login_date=?",
        (user_id, today.isoformat())
    ).fetchone()

    if not existing:
        conn.execute(
            "INSERT INTO login_activity (user_id, login_date) VALUES (?, ?)",
            (user_id, today.isoformat())
        )

    conn.commit()
    conn.close()

@app.route("/overview/edit", methods=["POST"])
def edit_task():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    task_id = request.form.get("id")
    name = request.form.get("name")
    description = request.form.get("description")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    conn.execute(
        "UPDATE habits SET name=?, description=?, start_date=?, end_date=? WHERE id=? AND user_id=?",
        (name, description, start_date, end_date, task_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/overview")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        action = request.form.get("action")
        conn = get_db()

        if action == "update_username":
            new_username = request.form.get("username", "").strip()

            if not new_username:
                conn.close()
                return render_error("settings.html", "Username cannot be empty!")
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (new_username,)
            ).fetchone()

            if existing:
                conn.close()
                return render_error("settings.html", "Username already taken!")

            conn.execute(
                "UPDATE users SET username = ? WHERE id = ?",
                (new_username, session["user_id"])
            )
            conn.commit()
            conn.close()

            return render_success("settings.html", "Username has been updated!")

        elif action == "change_password":
            current = request.form.get("current_password")
            new_pw  = request.form.get("new_password")
            confirm = request.form.get("confirm_password")

            user = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?",
                (session["user_id"],)
            ).fetchone()

            if not check_password_hash(user["password_hash"], current):
                conn.close()
                return render_error("settings.html", "Current password is incorrect!")

            if new_pw != confirm:
                conn.close()
                return render_error("settings.html", "New passwords do not match!")

            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (generate_password_hash(new_pw), session["user_id"])
            )
            conn.commit()
            conn.close()
            
            return render_success("settings.html", "Password changed successfully!")

        elif action == "reset_streaks":
            conn.execute(
                "UPDATE habits SET current_streak = 0, longest_streak = 0 WHERE user_id = ?",
                (session["user_id"],)
            )
            conn.commit()
            conn.close()

            flash("All streaks have been reset")
            return redirect("/settings")

        elif action == "clear_completions":
            conn.execute(
                "DELETE FROM completions WHERE user_id = ?",
                (session["user_id"],)
            )
            conn.commit()
            conn.close()

            flash("Completion history cleared")
            return redirect("/settings")

        elif action == "delete_account":
            conn.execute("DELETE FROM completions WHERE user_id = ?", (session["user_id"],))
            conn.execute("DELETE FROM habits WHERE user_id = ?", (session["user_id"],))
            conn.execute("DELETE FROM login_activity WHERE user_id = ?", (session["user_id"],))
            conn.execute("DELETE FROM password_resets WHERE user_id = ?", (session["user_id"],))
            conn.execute("DELETE FROM users WHERE id = ?", (session["user_id"],))
            conn.commit()
            conn.close()

            session.clear()
            return redirect("/register")
    conn = get_db()
    row = conn.execute(
        "SELECT username FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    conn.close()

    name = row["username"] if row else None

    return render_template("settings.html", name=name)
