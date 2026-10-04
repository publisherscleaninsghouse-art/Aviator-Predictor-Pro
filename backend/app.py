from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sqlite3
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "aviator.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            rounds INTEGER,
            risk TEXT,
            target REAL,
            predicted REAL,
            confidence INTEGER,
            risk_score INTEGER,
            recommendation TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            score REAL,
            confidence INTEGER,
            streak INTEGER,
            pnl REAL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    existing = conn.execute("SELECT COUNT(*) FROM rounds").fetchone()[0]
    if existing == 0:
        sample_values = [1.2, 1.6, 2.1, 1.7, 2.8, 2.3, 1.9, 3.4, 2.5, 1.8, 3.1, 2.2, 1.6, 2.7, 2.0]
        conn.executemany(
            "INSERT INTO rounds (value) VALUES (?)",
            [(float(v),) for v in sample_values],
        )

    leaderboard_seed = [
        ("Ganymed_Hack", 118.6, 84, 9, 66.4),
        ("NovaPilot", 101.2, 79, 7, 43.2),
        ("OrbitAI", 96.8, 75, 6, 30.4),
        ("ApexFlow", 88.9, 71, 5, 22.1),
    ]
    existing = conn.execute("SELECT COUNT(*) FROM leaderboard").fetchone()[0]
    if existing == 0:
        conn.executemany(
            "INSERT INTO leaderboard (name, score, confidence, streak, pnl) VALUES (?, ?, ?, ?, ?)",
            leaderboard_seed,
        )

    conn.commit()
    conn.close()


def calculate_round_data(window):
    conn = get_db_connection()
    if window == "last_1h":
        limit = 8
    elif window == "last_6h":
        limit = 12
    elif window == "last_7d":
        limit = 20
    else:
        limit = 15

    rows = conn.execute(
        "SELECT value, timestamp FROM rounds ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()

    values = [float(r["value"]) for r in reversed(rows)]
    if not values:
        values = [1.2, 1.5, 2.0, 1.8, 2.4]

    actual = values
    forecast = [round(v * (0.98 + (index * 0.01)), 2) for index, v in enumerate(actual)]
    chart = [{"time": f"T{index:02d}", "multiplier": round(actual[i], 2), "prediction": round(forecast[i], 2)} for i, index in enumerate(range(len(actual)))]
    return chart


def compute_prediction(rounds, risk, target):
    conn = get_db_connection()
    rows = conn.execute("SELECT value FROM rounds ORDER BY id DESC LIMIT ?", (rounds,)).fetchall()
    conn.close()

    values = [float(r["value"]) for r in rows]
    if not values:
        values = [1.2, 1.7, 2.1, 1.9, 2.5]

    avg = sum(values) / len(values)
    volatility = ((sum((v - avg) ** 2 for v in values) / len(values)) ** 0.5)

    risk_factor = {"low": 0.9, "medium": 1.0, "high": 1.15}.get(risk, 1.0)
    target_factor = float(target) or 2.0
    forecast = max(1.1, round((avg * 0.82 + target_factor * 0.45 + volatility * 0.2) * risk_factor, 2))
    confidence = int(max(58, min(96, 70 + (target_factor * 7) - (volatility * 9))))
    risk_score = int(max(18, min(91, 35 + volatility * 20 + ("medium" == risk) * 12 + ("high" == risk) * 18)))
    recommendation = "BULLISH" if forecast >= target_factor else "BEARISH"

    patterns = [
        {"name": "Momentum Pattern", "strength": min(95, max(40, int((avg * 18) + confidence / 2)))},
        {"name": "Volatility Shift", "strength": min(94, max(30, int(volatility * 23 + 22)))},
        {"name": "Support Level", "strength": min(97, max(35, int((target_factor * 16) + 30)))},
    ]

    return {
        "predicted": forecast,
        "confidence": confidence,
        "risk_score": risk_score,
        "recommendation": recommendation,
        "patterns": patterns,
    }


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})


@app.get("/api/dashboard")
def dashboard():
    conn = get_db_connection()
    latest_rounds = conn.execute("SELECT value FROM rounds ORDER BY id DESC LIMIT 15").fetchall()
    conn.close()

    values = [float(r["value"]) for r in latest_rounds]
    if not values:
        values = [1.2, 1.8, 2.4, 1.9, 2.8]

    avg = sum(values) / len(values)
    trend = round(((values[-1] - values[0]) / values[0]) * 100, 1)
    confidence = 78
    win_rate = round(62 + (avg * 2), 1)

    chart = calculate_round_data("last_24h")
    live_prediction = {
        "label": "Live Pattern Signal",
        "value": round(values[-1] * 1.10, 2),
        "confidence": confidence,
        "risk": "Medium",
    }

    return jsonify({
        "metrics": {
            "trend": trend,
            "confidence": confidence,
            "risk": "Medium",
            "winRate": win_rate,
            "totalRounds": 1245,
        },
        "chart": chart,
        "activePrediction": live_prediction,
        "stats": {
            "modelVersion": "v3.2.1",
            "lastUpdate": "2 sec ago",
            "dataPoints": 45230,
            "averageMultiplier": round(avg, 2),
        },
    })


@app.get("/api/leaderboard")
def leaderboard():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT name, score, confidence, streak, pnl FROM leaderboard ORDER BY score DESC LIMIT 10"
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@app.get("/api/analytics")
def analytics():
    conn = get_db_connection()
    rows = conn.execute("SELECT value FROM rounds ORDER BY id DESC LIMIT 30").fetchall()
    conn.close()

    values = [float(r["value"]) for r in rows]
    avg = sum(values) / len(values)
    variance = sum((x - avg) ** 2 for x in values) / len(values)
    volatility = round((variance ** 0.5), 2)

    return jsonify({
        "volatility": volatility,
        "averageMultiplier": round(avg, 2),
        "winRate": round((sum(1 for v in values if v >= 2.0) / len(values)) * 100, 1),
        "sessionCount": 18,
        "peakMultiplier": round(max(values), 2),
    })


@app.post("/api/predict")
def predict():
    payload = request.get_json(force=True, silent=True) or {}
    rounds = int(payload.get("rounds", 150))
    risk = (payload.get("risk", "medium") or "medium").lower()
    target = float(payload.get("target", 2.0) or 2.0)
    window = payload.get("window", "last_24h")

    result = compute_prediction(rounds, risk, target)

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO predictions (name, rounds, risk, target, predicted, confidence, risk_score, recommendation) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "Manual Prediction",
            rounds,
            risk,
            target,
            result["predicted"],
            result["confidence"],
            result["risk_score"],
            result["recommendation"],
        ),
    )
    conn.commit()
    conn.close()

    new_update = {
        "timestamp": datetime.utcnow().isoformat(),
        "trend": result["predicted"],
        "confidence": result["confidence"],
        "risk": risk,
    }
    socketio.emit("stats_update", new_update)

    return jsonify({
        "success": True,
        "prediction": result,
        "chart": calculate_round_data(window),
    })


@socketio.on("connect")
def handle_connect():
    emit("status", {"message": "Connected to Aviator Predictor stream"})


@socketio.on("request_stats")
def handle_stats_request():
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "trend": round(random.uniform(8, 18), 1),
        "confidence": random.randint(72, 94),
        "risk": random.choice(["Low", "Medium", "High"]),
    }
    emit("stats_update", payload)


if __name__ == "__main__":
    init_db()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
