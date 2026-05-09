from flask import Flask, request, jsonify
from core.orchestrator import Orchestrator
from security.auth import verify

app = Flask(__name__)
orch = Orchestrator()

@app.route("/")
def home():
    return {"message": "AICI Core Running"}

@app.route("/health")
def health():
    return {"status": "healthy"}

@app.route("/execute", methods=["POST"])
def execute():
    if not verify(request):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True)
    result = orch.run(data)
    return jsonify(result)
