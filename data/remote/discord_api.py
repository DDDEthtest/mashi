from datetime import datetime, timezone
import requests
from configs.config import APPLICATION_ID, DISCORD_TOKEN


def is_user_subscribed(user_id: int):
    url = f"https://discord.com/api/v10/applications/{APPLICATION_ID}/entitlements?user_id={user_id}"
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}"
    }

    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
        return False

    entitlements = resp.json()
    now = datetime.now(timezone.utc)

    for ent in entitlements:
        # Only subscription entitlements (type 8 = SUBSCRIPTION)
        if ent.get("type") != 8:
            continue

        # Must not be deleted (refunded / canceled)
        if ent["deleted"]:
            continue

        # Must not be expired
        if ent.get("ends_at"):
            ends = datetime.fromisoformat(ent["ends_at"].replace("Z", "+00:00"))
            if ends < now:
                continue

        # Valid active subscription found
        return True

    return False
