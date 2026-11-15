"""Sends phone alerts through ntfy.sh. The topic name is read from backend/.env."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()


def send_alert(message, title="Koleroga alert", priority="high"):
    topic = os.getenv("NTFY_TOPIC")
    if not topic:
        print("NTFY_TOPIC is not set, alert not sent:", message)
        return False
    try:
        r = requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Priority": priority, "Tags": "warning"},
            timeout=10,
        )
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        print("Alert failed:", e)
        return False


if __name__ == "__main__":
    print("sent:", send_alert("Test alert from the Koleroga system", title="Test"))
