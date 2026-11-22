def detect_fraud(message):

    text = message.lower()

    suspicious_patterns = {
        "account blocked": 25,
        "urgent": 10,
        "immediately": 10,
        "verify your account": 20,
        "share otp": 30,
        "upi pin": 25,
        "claim reward": 15,
        "bank details": 20,
        "click this link": 15,
        "kyc update": 15
    }

    score = 0
    detected = []

    for phrase, points in suspicious_patterns.items():

        if phrase in text:
            score += points
            detected.append(phrase)

    score = min(score, 100)

    if score >= 60:
        risk = "High Risk"

    elif score >= 20:
        risk = "Medium Risk"

    else:
        risk = "Low Risk"

    if detected:
        explanation = (
            "Suspicious indicators detected: "
            + ", ".join(detected)
        )
    else:
        explanation = "No listed suspicious patterns detected."

    return {
        "risk_score": score,
        "risk_level": risk,
        "detected_patterns": detected,
        "explanation": explanation
    }