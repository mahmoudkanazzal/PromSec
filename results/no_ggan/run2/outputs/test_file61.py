import os
import json
import logging
import MySQLdb
from MySQLdb.constants import SSL
from contextlib import closing
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
app.config["PROPAGATE_EXCEPTIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

def _get_db_connection():
    required = ["DB_HOST", "DB_USER", "DB_PASS", "DB_NAME", "DB_SSL_CA"]
    missing = [var for var in required if var not in os.environ]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    host = os.environ["DB_HOST"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASS"]
    db = os.environ["DB_NAME"]
    ca_path = os.environ["DB_SSL_CA"]
    if not (os.path.isfile(ca_path) and os.access(ca_path, os.R_OK)):
        raise RuntimeError("SSL CA file is missing or not readable")
    ssl_options = {"ca": ca_path, "cert_reqs": SSL.CERT_REQUIRED, "verify_server_cert": True}
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, ssl=ssl_options, charset="utf8mb4", use_unicode=True, connect_timeout=10, autocommit=True)

def _validate_coordinates(lat, lon):
    if not (-90.0 <= lat <= 90.0):
        raise ValueError("Latitude out of range")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError("Longitude out of range")

@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.route("/api/temperature_for_location", methods=["POST"])
def temperature_for_location():
    if not request.is_json:
        return jsonify(error="Content-Type must be application/json"), 415
    try:
        payload = request.get_json()
        if not isinstance(payload, dict):
            raise ValueError("Payload is not a JSON object")
        lat = payload.get("lat")
        lon = payload.get("lon")
        date = payload.get("date")
        if not isinstance(lat, (int, float)):
            raise ValueError("lat must be a number")
        if not isinstance(lon, (int, float)):
            raise ValueError("lon must be a number")
        if not isinstance(date, int):
            raise ValueError("date must be an integer")
        _validate_coordinates(float(lat), float(lon))
        if date < 0:
            raise ValueError("date must be non-negative")
    except Exception as e:
        logger.warning("Invalid request payload: %s", e)
        return jsonify(error="malformed payload"), 400
    try:
        with closing(_get_db_connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = "SELECT temp FROM temperature WHERE lat=%s AND lon=%s AND date=%s LIMIT 1"
                cursor.execute(query, (float(lat), float(lon), int(date)))
                row = cursor.fetchone()
                if row is None:
                    return jsonify(error="temperature not found"), 404
                return jsonify(temp=row[0]), 200
    except MySQLdb.Error as e:
        logger.error("Database error: %s", e, exc_info=True)
        return jsonify(error="internal server error"), 500

if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port_str = os.getenv("FLASK_PORT", "5000")
    try:
        port = int(port_str)
        if not (1 <= port <= 65535):
            port = 5000
    except Exception:
        port = 5000
    app.run(host=host, port=port, debug=False)