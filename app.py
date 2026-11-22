from flask import Flask, render_template, request, jsonify
from urllib.parse import urlparse
import ipaddress
import cv2
import numpy as np

from fraud_detection import detect_fraud
from ai_detector import analyze_message
from database import init_db, save_scan, get_analytics

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/scan", methods=["POST"])
def scan_message():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Invalid JSON request."}), 400

        message = data.get("message", "")

        if not isinstance(message, str) or not message.strip():
            return jsonify({"error": "Please enter a valid message."}), 400

        rule_result = detect_fraud(message)
        ai_result = analyze_message(message)

        result = {
            "risk_score": rule_result["risk_score"],
            "risk_level": rule_result["risk_level"],
            "detected_patterns": rule_result["detected_patterns"],
            "explanation": rule_result["explanation"],
            "ai_available": ai_result["available"],
            "ai_analysis": ai_result["analysis"]
        }

        # Save message scan in SQLite database
        save_scan(
            scan_type="Message",
            scanned_content=message,
            risk_score=rule_result["risk_score"],
            risk_level=rule_result["risk_level"],
            detected_patterns=rule_result["detected_patterns"],
            explanation=rule_result["explanation"]
        )

        return jsonify(result), 200

    except Exception:
        app.logger.exception("Message scanning failed")

        return jsonify({
            "error": "An error occurred while scanning the message."
        }), 500



@app.route("/check-link", methods=["POST"])
def check_payment_link():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Invalid JSON request."}), 400

        link = data.get("url", "")

        if not isinstance(link, str) or not link.strip():
            return jsonify({"error": "Please enter a valid payment link."}), 400

        link = link.strip()

        if len(link) > 2048:
            return jsonify({"error": "The payment link is too long."}), 400

        warnings = []
        score = 0

        parsed = urlparse(link)

        if parsed.scheme not in ("http", "https"):
            warnings.append("Only HTTP and HTTPS links are supported.")
            score += 40

        if not parsed.hostname:
            warnings.append("The link does not contain a valid website address.")
            score += 40

        if parsed.username or parsed.password:
            warnings.append("The link contains embedded login credentials.")
            score += 40

        hostname = parsed.hostname or ""

        try:
            ipaddress.ip_address(hostname)
            warnings.append(
                "The link uses an IP address instead of a normal domain name."
            )
            score += 30
        except ValueError:
            pass

        if "xn--" in hostname.lower():
            warnings.append(
                "The domain contains an encoded international character sequence."
            )
            score += 25

        if len(hostname.split(".")) > 4:
            warnings.append(
                "The website address contains many subdomains."
            )
            score += 15

        suspicious_words = [
            "verify-account",
            "urgent-payment",
            "claim-prize",
            "free-reward",
            "account-suspended",
            "login-verify"
        ]

        lower_link = link.lower()

        for word in suspicious_words:
            if word in lower_link:
                warnings.append(
                    "Suspicious keyword found in link: " + word
                )
                score += 20

        score = min(score, 100)

        if score >= 60:
            risk_level = "High Risk"
        elif score >= 20:
            risk_level = "Medium Risk"
        else:
            risk_level = "Low Risk"

        if warnings:
            explanation = (
                "Potential warning signs were detected in this link."
            )
        else:
            explanation = (
                "No basic warning signs were detected. "
                "This does not guarantee that the link is safe."
            )

        return jsonify({
            "checked_url": link,
            "risk_score": score,
            "risk_level": risk_level,
            "is_suspicious": score >= 20,
            "warnings": warnings,
            "explanation": explanation
        }), 200

    except Exception:
        app.logger.exception("Payment link checking failed")

        return jsonify({
            "error": "An error occurred while checking the payment link."
        }), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "UPI Shield AI backend is running"
    })
def decode_qr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # white border helps the detector a lot
    padded = cv2.copyMakeBorder(gray, 40, 40, 40, 40,
                                cv2.BORDER_CONSTANT, value=255)
    variants = [image, gray, padded]
    for scale in (2, 3, 0.5):
        variants.append(cv2.resize(padded, None, fx=scale, fy=scale,
                                   interpolation=cv2.INTER_CUBIC))
    variants.append(cv2.threshold(padded, 0, 255,
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])

    detector = cv2.QRCodeDetector()
    for v in variants:
        text, _, _ = detector.detectAndDecode(v)
        if text:
            return text
    return None


def analyze_qr_content(content):
    warnings, score = [], 0
    lower = content.lower()

    if lower.startswith("upi://"):
        from urllib.parse import parse_qs
        params = parse_qs(urlparse(content).query)
        payee = params.get("pa", [""])[0]
        if not payee or "@" not in payee:
            warnings.append("UPI ID is missing or invalid.")
            score += 40
        if "am" in params:
            warnings.append("QR has a pre-filled payment amount.")
            score += 20
        if "mc" not in params:
            warnings.append("No merchant code; may be a personal account.")
            score += 10
    elif lower.startswith(("http://", "https://")):
        parsed = urlparse(content)
        host = parsed.hostname or ""
        if parsed.scheme == "http":
            warnings.append("Link is not encrypted (HTTP).")
            score += 25
        try:
            ipaddress.ip_address(host)
            warnings.append("Link uses an IP address instead of a domain.")
            score += 30
        except ValueError:
            pass
        if "xn--" in host:
            warnings.append("Domain has encoded international characters.")
            score += 25
        for w in ["verify-account", "urgent-payment", "claim-prize",
                  "free-reward", "account-suspended", "login-verify"]:
            if w in lower:
                warnings.append("Suspicious keyword: " + w)
                score += 20
    else:
        warnings.append("QR contains unknown content, not a UPI or web link.")
        score += 30

    score = min(score, 100)
    level = "High Risk" if score >= 60 else "Medium Risk" if score >= 20 else "Low Risk"
    return score, level, warnings

@app.route("/check-qr", methods=["POST"])
def check_qr_code():
    try:
        if "qr_image" not in request.files:
            return jsonify({"error": "Please upload a QR code image."}), 400

        file = request.files["qr_image"]
        image_bytes = file.read()
        if not image_bytes:
            return jsonify({"error": "The uploaded image is empty."}), 400

        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8),
                             cv2.IMREAD_COLOR)
        if image is None:
            return jsonify({"error": "Invalid image file."}), 400

        content = decode_qr(image)
        if not content:
            return jsonify({
                "qr_found": False,
                "message": "No readable QR code was found in this image."
            }), 200

        score, level, warnings = analyze_qr_content(content)
        return jsonify({
            "qr_found": True,
            "decoded_content": content,
            "risk_score": score,
            "risk_level": level,
            "warnings": warnings
        }), 200

    except Exception:
        app.logger.exception("QR code scanning failed")
        return jsonify({"error": "An error occurred while scanning the QR code."}), 500

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )