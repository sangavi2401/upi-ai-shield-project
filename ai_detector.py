import requests


def analyze_message(message):

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:3b",
                "prompt": (
                    "You are a UPI fraud detection assistant. "
                    "Analyze the following message for possible "
                    "banking or UPI scams. Identify suspicious "
                    "indicators and explain them in simple language. "
                    "Never ask for OTP, UPI PIN or passwords.\n\n"
                    "Message: " + message
                ),
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        return {
            "available": True,
            "analysis": result.get("response", "").strip()
        }

    except Exception as e:

        print("OLLAMA ERROR:", str(e))

        return {
            "available": False,
            "analysis": "Local AI analysis is temporarily unavailable."
        }