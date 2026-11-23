import os
import logging
import json
import traceback
import ssl
from flask import Flask, request, abort, make_response, jsonify
import MySQLdb
from MySQLdb.cursors import DictCursor

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logger.addHandler(handler)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_SSL_CA = os.getenv("DB_SSL_CA")

if not all([DB_USER, DB_PASSWORD, DB_NAME, DB_SSL_CA]):
    logger.error("Database configuration is incomplete")
    raise RuntimeError("Database configuration is incomplete")

app = Flask(__name__)
app.config.update({
    "MAX_CONTENT_LENGTH": 1024,
    "SESSION_COOKIE_SECURE": True,
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SAMESITE": "Strict",
    "PREFERRED_URL_SCHEME": "https",
    "DEBUG": False,
    "TESTING": False,
    "JSONIFY_MIMETYPE": "application/json",
    "JSON_SORT_KEYS": False,
    "JSONIFY_PRETTYPRINT_REGULAR": False,
    "JSON_AS_ASCII": False
})

@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none';"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    return response

def _handle_error(error, default_msg):
    description = getattr(error, "description", default_msg)
    status = getattr(error, "code", 500)
    return make_response(jsonify(error=description), status)

for code, msg in [(400, "Bad request"), (404, "Not found"), (415, "Unsupported Media Type"), (413, "Payload too large"), (500, "Internal server error")]:
    app.register_error_handler(code, lambda e, m=msg: _handle_error(e, m))

def _validate_int(value, name, min_val=None, max_val=None):
    try:
        iv = int(value)
    except Exception:
        abort(400, description=f"Invalid parameter: {name}")
    if (min_val is not None and iv < min_val) or (max_val is not None and iv > max_val):
        abort(400, description=f"Parameter out of range: {name}")
    return iv

def _parse_payload(raw_payload):
    try:
        data = json.loads(raw_payload)
    except Exception:
        abort(400, description="Invalid JSON payload")
    if not isinstance(data, dict):
        abort(400, description="JSON payload must be an object")
    return data

def _get_db_connection():
    ssl_context = ssl.create_default_context(cafile=DB_SSL_CA)
    ssl_context.check_hostname = True
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_params = {"ca": DB_SSL_CA, "cert_reqs": ssl.CERT_REQUIRED, "ssl_context": ssl_context}
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME,
                           charset="utf8mb4", use_unicode=True, cursorclass=DictCursor,
                           autocommit=True, connect_timeout=5, ssl=ssl_params)

@app.route("/api/temperature_for_location", methods=["GET", "POST"])
def temperature_for_location():
    if request.method == "GET":
        raw = request.args.get("payload")
        if raw is None:
            abort(400, description="Missing payload")
        if len(raw.encode("utf-8")) > app.config["MAX_CONTENT_LENGTH"]:
            abort(413, description="Payload too large")
        payload = _parse_payload(raw)
    else:
        ct = request.headers.get("Content-Type", "")
        if not ct.lower().startswith("application/json"):
            abort(415, description="Unsupported Media Type")
        json_body = request.get_json(force=False, silent=False)
        if not isinstance(json_body, dict):
            abort(400, description="Invalid JSON payload")
        raw = json.dumps(json_body, separators=(",", ":"))
        if len(raw.encode("utf-8")) > app.config["MAX_CONTENT_LENGTH"]:
            abort(413, description="Payload too large")
        payload = json_body
    for key in ("lat", "lon", "date"):
        if key not in payload:
            abort(400, description=f"Missing parameter: {key}")
    lat = _validate_int(payload["lat"], "lat", -90, 90)
    lon = _validate_int(payload["lon"], "lon", -180, 180)
    date = _validate_int(payload["date"], "date", 0, None)
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT temp FROM temperature WHERE lat=%s AND lon=%s AND date=%s LIMIT 1", (lat, lon, date))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    except MySQLdb.Error:
        logger.error("Database error: %s", traceback.format_exc())
        abort(500, description="Internal server error")
    if row and "temp" in row:
        resp = make_response(str(row["temp"]))
        resp.headers["Content-Type"] = "text/plain; charset=utf-8"
        return resp
    else:
        abort(404, description="Temperature data not found")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)