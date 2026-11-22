import sqlite3
import json
import os
from datetime import datetime

# Database file location
DATABASE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "upi_shield.db"
)


# Connect to SQLite database
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# Create database table
def init_db():

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            scan_type TEXT NOT NULL,

            scanned_content TEXT NOT NULL,

            risk_score INTEGER NOT NULL,

            risk_level TEXT NOT NULL,

            detected_patterns TEXT,

            explanation TEXT,

            created_at TEXT NOT NULL

        )
    """)

    connection.commit()
    connection.close()

    print("UPI Shield AI database initialized successfully.")


# Save scan results
def save_scan(
    scan_type,
    scanned_content,
    risk_score,
    risk_level,
    detected_patterns,
    explanation
):

    connection = get_connection()

    connection.execute("""
        INSERT INTO scan_history (
            scan_type,
            scanned_content,
            risk_score,
            risk_level,
            detected_patterns,
            explanation,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        scan_type,
        scanned_content,
        risk_score,
        risk_level,
        json.dumps(detected_patterns),
        explanation,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    connection.commit()
    connection.close()


# Get security analytics
def get_analytics():

    connection = get_connection()

    statistics = connection.execute("""
        SELECT

            COUNT(*) AS total_scans,

            SUM(CASE
                WHEN risk_score >= 20 THEN 1
                ELSE 0
            END) AS fraud_alerts,

            SUM(CASE
                WHEN risk_score >= 60 THEN 1
                ELSE 0
            END) AS high_risk,

            SUM(CASE
                WHEN risk_score >= 20 AND risk_score < 60 THEN 1
                ELSE 0
            END) AS medium_risk,

            SUM(CASE
                WHEN risk_score < 20 THEN 1
                ELSE 0
            END) AS low_risk,

            SUM(CASE
                WHEN scan_type = 'Message' THEN 1
                ELSE 0
            END) AS message_scans,

            SUM(CASE
                WHEN scan_type = 'Payment Link' THEN 1
                ELSE 0
            END) AS payment_link_scans

        FROM scan_history
    """).fetchone()

    recent_scans = connection.execute("""
        SELECT *
        FROM scan_history
        ORDER BY id DESC
        LIMIT 10
    """).fetchall()

    connection.close()

    return {
        "total_scans": statistics["total_scans"] or 0,
        "fraud_alerts": statistics["fraud_alerts"] or 0,
        "high_risk": statistics["high_risk"] or 0,
        "medium_risk": statistics["medium_risk"] or 0,
        "low_risk": statistics["low_risk"] or 0,
        "message_scans": statistics["message_scans"] or 0,
        "payment_link_scans": statistics["payment_link_scans"] or 0,
        "recent_scans": [
            dict(scan) for scan in recent_scans
        ]
    }