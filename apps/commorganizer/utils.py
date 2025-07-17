import requests


def send_discord_webhook(webhook_url, message):
    try:
        payload = {"content": message}
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"Discord webhook failed: {e}")
