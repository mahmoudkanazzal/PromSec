import os
import MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, abort, make_response
from contextlib import closing

_DUMMY_HASH = generate_password_hash("dummy_password")
MAX_USERNAME_LENGTH = 150
MAX_PASSWORD_LENGTH = 256


def get_db_connection():
    env_vars = {
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "DB_NAME": os.getenv("DB_NAME"),
    }
    missing = [key for key, value in env_vars.items() if not value]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    return MySQLdb.connect(
        host=env_vars["DB_HOST"],
        user=env_vars["DB_USER"],
        password=env_vars["DB_PASSWORD"],
        db=env_vars["DB_NAME"],
        charset="utf8mb4",
        use_unicode=True,
        autocommit=True,
    )


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(24)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if (
        not username
        or not password
        or len(username) > MAX_USERNAME_LENGTH
        or len(password) > MAX_PASSWORD_LENGTH
    ):
        return make_response("Invalid credentials", 400)
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("SELECT password FROM user WHERE username = %s", (username,))
                row = cur.fetchone()
                stored_hash = row[0] if row else _DUMMY_HASH
    except (MySQLdb.OperationalError, MySQLdb.ProgrammingError, MySQLdb.InterfaceError):
        return make_response("Invalid credentials", 401)
    if not check_password_hash(stored_hash, password):
        return make_response("Invalid credentials", 401)
    return make_response("Login Success", 200)


if __name__ == "__main__":
    app.run()