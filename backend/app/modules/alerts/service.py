import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alerts.channels import EmailChannel, WebhookChannel
from app.modules.alerts.models import AlertChannel, AlertHistory, AlertSubscription


async def dispatch(
    db: AsyncSession,
    rule_id: uuid.UUID,
    subject: str,
    body: str,
    context: dict | None = None,
) -> list[dict]:
    result = await db.execute(
        select(AlertSubscription).where(
            AlertSubscription.rule_id == rule_id,
            AlertSubscription.active == True,
        )
    )
    subscriptions = result.scalars().all()

    if not subscriptions:
        return []

    results = []
    for sub in subscriptions:
        ch_result = await db.execute(
            select(AlertChannel).where(AlertChannel.id == sub.channel_id)
        )
        channel = ch_result.scalar_one_or_none()
        if not channel or not channel.active:
            continue

        if channel.type == "email":
            ch_impl = EmailChannel(channel.config or {})
        elif channel.type == "webhook":
            ch_impl = WebhookChannel(channel.config or {})
        else:
            continue

        success = await ch_impl.send(subject, body)

        history = AlertHistory(
            channel_id=channel.id,
            rule_id=rule_id,
            subject=subject,
            body=body,
            status="sent" if success else "failed",
            sent_at=datetime.now(timezone.utc) if success else None,
        )
        db.add(history)

        results.append({
            "channel_id": str(channel.id),
            "channel_type": channel.type,
            "status": "sent" if success else "failed",
        })

    await db.flush()
    return results
