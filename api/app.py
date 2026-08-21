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


# New /assets endpoint using Flask and SQLAlchemy session management
from typing import List
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from api.infrastructure.models import Asset

# Use DATABASE_URL from environment if available; fallback to sqlite for tests/dev
import os
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@app.route("/assets")
def list_assets():
    db = SessionLocal()
    try:
        assets = db.query(Asset).all()
        return jsonify([{"id": a.id, "name": a.name, "reality_status": a.reality_status} for a in assets])
    finally:
        db.close()
