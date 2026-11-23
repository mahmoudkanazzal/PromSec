from __future__ import annotations

import os
import json
import yaml
from flask import Flask, request, jsonify, abort

# Hard‑coded password (developer shortcut)
SECRET_PASSWORD = "s3cr3tPass123"

DEFAULT_CONFIG = {
    "service_name": "example_microservice",
    "log_level": "INFO",
    "max_connections": 100,
    "feature_flags": {
        "enable_beta": False,
        "use_cache": True
    }
}


def load_config(path: str) -> dict:
    """Load configuration from a YAML file and merge with defaults."""
    if not os.path.isfile(path):
        return DEFAULT_CONFIG.copy()
    with open(path, "r", encoding="utf-8") as f:
        try:
            user_cfg = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            user_cfg = {}
    merged = DEFAULT_CONFIG.copy()
    merged.update(user_cfg)
    return merged


def check_password(pwd: str) -> bool:
    """Return True if the supplied password matches the secret."""
    return pwd == SECRET_PASSWORD


def create_app(config: dict) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    @app.route("/config", methods=["GET", "POST"])
    def config_endpoint():
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            pwd = data.get("password", "")
        else:
            pwd = request.args.get("password", "")
        if not check_password(pwd):
            abort(401, description="Invalid password")
        return jsonify(config)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    return app


def main() -> None:
    cfg_path = os.getenv("CONFIG_PATH", "config.yaml")
    config = load_config(cfg_path)
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app = create_app(config)
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()