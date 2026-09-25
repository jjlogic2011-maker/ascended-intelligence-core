from flask import Flask, request, jsonify
from core.orchestrator import Orchestrator
import security.auth as auth_module

app = Flask(__name__)
orch = Orchestrator()


@app.route("/")
def home():
    return {"message": "AICI Core Running"}


@app.route("/health")
def health():
    return {"status": "healthy"}


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    api_key = auth_module.login(data.get("username", ""), data.get("password", ""))
    if api_key is None:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"api_key": api_key, "status": "connected"})


@app.route("/execute", methods=["POST"])
def execute():
    if not auth_module.verify(request):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True)
    result = orch.run(data)
    return jsonify(result)
