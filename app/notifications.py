import logging
from datetime import datetime, timezone
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


def send_user_notification(event_type: str, user_data: dict) -> None:
    """
    Best-effort Slack notification. This function deliberately never raises:
    notification outages must not turn a committed CRUD operation into an API failure.
    """
    webhook_url = get_settings().slack_webhook_url
    if not webhook_url:
        logger.info("Slack webhook not configured; skipped %s notification.", event_type)
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    details = (
        f"*Event:* `{event_type}`\n"
        f"*User:* {user_data.get('name', 'N/A')}\n"
        f"*Email:* {user_data.get('email', 'N/A')}\n"
        f"*Role:* {user_data.get('role', 'N/A')}\n"
        f"*User ID:* `{user_data.get('id', 'N/A')}`\n"
        f"*Time:* {timestamp}"
    )

    try:
        response = httpx.post(
            webhook_url,
            json={"text": details},
            timeout=5.0,
        )
        response.raise_for_status()
        logger.info("Slack notification sent: %s", event_type)
    except httpx.HTTPError:
        logger.exception("Slack notification failed for event %s.", event_type)
    except Exception:
        logger.exception("Unexpected notification error for event %s.", event_type)
