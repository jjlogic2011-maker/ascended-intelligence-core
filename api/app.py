from flask import Flask, request, jsonify
from core.orchestrator import Orchestrator

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
    data = request.json
    result = orch.run(data)
    return jsonify(result)