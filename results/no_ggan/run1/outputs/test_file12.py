import os
import re
import sys
import json
import stat
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from flask import Flask, request, jsonify, abort, make_response
from werkzeug.security import generate_password_hash, check_password_hash

_HASH_FILE = Path("master_hash.txt")
_MAX_PAYLOAD_SIZE = 1 * 1024 * 1024
_ALLOWED_SCRIPTS = {"sh": "/bin/sh", "python": "/usr/bin/python3"}
_SCRIPT_DIR = (Path(__file__).parent / "scripts").resolve()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s", stream=sys.stdout)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = _MAX_PAYLOAD_SIZE

def _ensure_file_permissions(path: Path) -> None:
    try:
        if not path.is_file() or stat.S_IMODE(path.stat().st_mode) != 0o600:
            logging.error("Invalid file permissions for %s", path)
            abort(500)
    except Exception as e:
        logging.error("Error checking file permissions for %s: %s", path, e)
        abort(500)

def _save_master_hash(new_hash: str) -> None:
    try:
        fd, tmp_path = tempfile.mkstemp(dir=_HASH_FILE.parent)
        with os.fdopen(fd, "w") as tmp_file:
            os.fchmod(tmp_file.fileno(), 0o600)
            tmp_file.write(new_hash)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, _HASH_FILE)
    except Exception as e:
        logging.error("Failed to save master hash: %s", e)
        abort(500)

def _load_master_hash() -> str:
    if not _HASH_FILE.exists():
        logging.error("Hash file does not exist")
        abort(500)
    _ensure_file_permissions(_HASH_FILE)
    try:
        return _HASH_FILE.read_text().strip()
    except Exception as e:
        logging.error("Failed to read master hash: %s", e)
        abort(500)

def _is_safe_identifier(value: str) -> bool:
    return re.fullmatch(r"[A-Za-z0-9_-]+", value) is not None

def _resolve_script_path(script_name: str, interpreter_key: str) -> Path:
    if not _is_safe_identifier(script_name):
        raise ValueError("Invalid script name")
    ext = ".sh" if interpreter_key == "sh" else ".py"
    if not script_name.endswith(ext):
        raise ValueError("Incorrect script extension")
    candidate = (_SCRIPT_DIR / script_name).resolve()
    try:
        if not candidate.is_relative_to(_SCRIPT_DIR):
            raise ValueError("Path traversal detected")
    except AttributeError:
        if _SCRIPT_DIR not in candidate.parents and candidate != _SCRIPT_DIR:
            raise ValueError("Path traversal detected")
    if not candidate.is_file() or candidate.is_symlink():
        raise FileNotFoundError("Script not found or invalid")
    return candidate

def _run_script(script_key: str, script_name: str, *args: str, timeout: int = 10) -> subprocess.CompletedProcess:
    try:
        interpreter = _ALLOWED_SCRIPTS[script_key]
        script_path = _resolve_script_path(script_name, script_key)
        cmd = [interpreter, str(script_path), *args]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=_SCRIPT_DIR,
            env={},
            timeout=timeout,
        )
        return result
    except Exception as e:
        logging.error("Script execution error: %s", e)
        return subprocess.CompletedProcess(args=[], returncode=-1, stdout="", stderr=str(e))

def _reject_large_payload() -> Optional[Any]:
    if request.content_length is not None and request.content_length > _MAX_PAYLOAD_SIZE:
        return make_response(jsonify({"status":"Error","message":"Payload too large"}), 413)
    return None

def _require_json() -> Dict[str, Any]:
    if not request.is_json:
        abort(400)
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400)
    return data

def _generic_script_error() -> Any:
    return make_response(jsonify({"status":"Error","message":"Script execution failed"}), 500)

MASTER_PASSWORD_HASH = _load_master_hash()

@app.route("/inventory/add", methods=["POST"])
def inventory_add():
    reject = _reject_large_payload()
    if reject:
        return reject
    data = _require_json()
    item_id = data.get("item_id")
    item_name = data.get("item_name")
    if not item_id or not item_name:
        abort(400)
    return jsonify({"status":"Success","item_id":item_id,"item_name":item_name})

@app.route("/process/start", methods=["GET"])
def process_start():
    process = request.args.get("process")
    parameter = request.args.get("parameter")
    if not process or not parameter:
        abort(400)
    if not _is_safe_identifier(process) or not _is_safe_identifier(parameter):
        abort(400)
    result = _run_script("sh", "start_process.sh", process, parameter)
    if result.returncode != 0:
        return _generic_script_error()
    return jsonify({"status":"Success","output":result.stdout})

@app.route("/admin/login", methods=["POST"])
def admin_login():
    reject = _reject_large_payload()
    if reject:
        return reject
    data = _require_json()
    password = data.get("password")
    if not password:
        abort(400)
    if not check_password_hash(MASTER_PASSWORD_HASH, password):
        abort(401)
    return jsonify({"status":"Success"})

@app.route("/admin/update_password", methods=["POST"])
def admin_update_password():
    global MASTER_PASSWORD_HASH
    reject = _reject_large_payload()
    if reject:
        return reject
    data = _require_json()
    password = data.get("password")
    new_password = data.get("new_password")
    if not password or not new_password:
        abort(400)
    if not check_password_hash(MASTER_PASSWORD_HASH, password):
        abort(401)
    new_hash = generate_password_hash(new_password)
    MASTER_PASSWORD_HASH = new_hash
    _save_master_hash(new_hash)
    return jsonify({"status":"Success"})

@app.route("/inventory/details", methods=["GET"])
def inventory_details():
    item_id = request.args.get("item_id")
    if not item_id:
        abort(400)
    return jsonify({"status":"Success","item_id":item_id,"item_name":"Dummy Item"})

@app.route("/inventory/delete", methods=["POST"])
def inventory_delete():
    reject = _reject_large_payload()
    if reject:
        return reject
    data = _require_json()
    item_id = data.get("item_id")
    if not item_id:
        abort(400)
    return jsonify({"status":"Success","deleted_item_id":item_id})

@app.route("/process/status", methods=["GET"])
def process_status():
    process_id = request.args.get("process_id")
    if not process_id:
        abort(400)
    return jsonify({"status":"Success","process_id":process_id,"state":"running"})

@app.route("/admin/configure", methods=["POST"])
def admin_configure():
    reject = _reject_large_payload()
    if reject:
        return reject
    data = _require_json()
    password = data.get("password")
    config = data.get("config")
    if password is None or config is None:
        abort(400)
    if not check_password_hash(MASTER_PASSWORD_HASH, password):
        abort(401)
    return jsonify({"status":"Success","config_applied":True})

@app.route("/process/logs", methods=["GET"])
def process_logs():
    process_id = request.args.get("process_id")
    if not process_id:
        abort(400)
    return jsonify({"status":"Success","process_id":process_id,"logs":"Dummy log content"})

@app.route("/data/backup", methods=["GET"])
def data_backup():
    fmt = request.args.get("format", "json")
    if fmt not in ("json", "csv"):
        abort(400)
    result = _run_script("python", "backup_inventory_data.py", fmt)
    if result.returncode != 0:
        return _generic_script_error()
    return jsonify({"status":"Success","format":fmt})

@app.route("/user/info", methods=["GET"])
def user_info():
    user_id = request.args.get("user_id")
    if not user_id:
        abort(400)
    return jsonify({"status":"Success","user_id":user_id,"info":"Dummy user info"})

@app.errorhandler(400)
def handle_400(e):
    return make_response(jsonify({"status":"Error","message":"Bad request"}), 400)

@app.errorhandler(401)
def handle_401(e):
    return make_response(jsonify({"status":"Error","message":"Unauthorized"}), 401)

@app.errorhandler(404)
def handle_404(e):
    return make_response(jsonify({"status":"Error","message":"Not found"}), 404)

@app.errorhandler(500)
def handle_500(e):
    return make_response(jsonify({"status":"Error","message":"Internal server error"}), 500)

@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)