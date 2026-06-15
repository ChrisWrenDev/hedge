import uuid
from datetime import datetime, timezone

import pytest


# ── Alert Model Tests ───────────────────────────────────────────

class TestAlertChannelModel:
    @pytest.mark.asyncio
    async def test_create_email_channel(self, db_session):
        from app.modules.alerts.models import AlertChannel
        ch = AlertChannel(
            name="Ops Email",
            type="email",
            config={
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@gmail.com",
                "password": "pass",
                "from_addr": "test@gmail.com",
                "to_addrs": ["ops@example.com"],
            },
            active=True,
        )
        db_session.add(ch)
        await db_session.flush()
        assert ch.id is not None
        assert ch.type == "email"

    @pytest.mark.asyncio
    async def test_create_webhook_channel(self, db_session):
        from app.modules.alerts.models import AlertChannel
        ch = AlertChannel(
            name="Slack",
            type="webhook",
            config={
                "url": "https://hooks.slack.com/test",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
            },
            active=True,
        )
        db_session.add(ch)
        await db_session.flush()
        assert ch.id is not None

    @pytest.mark.asyncio
    async def test_create_subscription(self, db_session):
        from app.modules.alerts.models import AlertChannel, AlertSubscription
        ch = AlertChannel(name="Test", type="webhook", config={}, active=True)
        db_session.add(ch)
        await db_session.flush()

        # Use a valid rule_id UUID (won't FK check in SQLite)
        rule_id = uuid.uuid4()
        sub = AlertSubscription(channel_id=ch.id, rule_id=rule_id, active=True)
        db_session.add(sub)
        await db_session.flush()
        assert sub.id is not None

    @pytest.mark.asyncio
    async def test_create_alert_history(self, db_session):
        from app.modules.alerts.models import AlertChannel, AlertHistory
        ch = AlertChannel(name="Test", type="webhook", config={}, active=True)
        db_session.add(ch)
        await db_session.flush()

        rule_id = uuid.uuid4()
        hist = AlertHistory(
            channel_id=ch.id,
            rule_id=rule_id,
            subject="Delta Alert",
            body="Delta exceeded threshold",
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )
        db_session.add(hist)
        await db_session.flush()
        assert hist.id is not None


# ── Alert Channel Tests ─────────────────────────────────────────

class TestChannels:
    def test_email_channel_send(self):
        from app.modules.alerts.channels import EmailChannel
        ch = EmailChannel({
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "username": "u",
            "password": "p",
            "from_addr": "from@test.com",
            "to_addrs": ["to@test.com"],
        })
        # Just verify it doesn't crash on construction
        assert ch.config["smtp_host"] == "smtp.test.com"

    def test_webhook_channel_send(self):
        from app.modules.alerts.channels import WebhookChannel
        ch = WebhookChannel({
            "url": "https://hooks.slack.com/test",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
        })
        assert ch.config["url"] == "https://hooks.slack.com/test"


# ── Alert Service Tests ─────────────────────────────────────────

class TestAlertService:
    @pytest.mark.asyncio
    async def test_dispatch_to_subscribed_channels(self, db_session):
        from app.modules.alerts.models import AlertChannel, AlertSubscription, AlertHistory
        from app.modules.alerts.service import dispatch

        rule_id = uuid.uuid4()
        ch = AlertChannel(name="Test WH", type="webhook", config={"url": "x"}, active=True)
        db_session.add(ch)
        await db_session.flush()

        sub = AlertSubscription(channel_id=ch.id, rule_id=rule_id, active=True)
        db_session.add(sub)
        await db_session.commit()

        results = await dispatch(
            db_session,
            rule_id=rule_id,
            subject="Alert",
            body="Something happened",
            context={"net_delta": 0.20},
        )
        assert len(results) >= 1
        assert results[0]["channel_id"] == str(ch.id)

    @pytest.mark.asyncio
    async def test_dispatch_no_subscriptions(self, db_session):
        from app.modules.alerts.service import dispatch
        results = await dispatch(
            db_session,
            rule_id=uuid.uuid4(),
            subject="x", body="y", context={},
        )
        assert results == []


# ── Alert API Tests ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_alert_channel(client):
    resp = await client.post("/api/alerts/channels", json={
        "name": "Test",
        "type": "webhook",
        "config": {"url": "https://hooks.slack.com/test"},
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Test"


@pytest.mark.asyncio
async def test_list_alert_channels(client):
    await client.post("/api/alerts/channels", json={
        "name": "A", "type": "webhook", "config": {"url": "x"},
    })
    resp = await client.get("/api/alerts/channels")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_list_alert_history(client):
    resp = await client.get("/api/alerts/history")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_subscription(client):
    create_ch = await client.post("/api/alerts/channels", json={
        "name": "Sub Test", "type": "webhook", "config": {"url": "x"},
    })
    ch_id = create_ch.json()["id"]
    rule_id = str(uuid.uuid4())

    resp = await client.post("/api/alerts/subscriptions", json={
        "channel_id": ch_id,
        "rule_id": rule_id,
    })
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_list_subscriptions(client):
    resp = await client.get("/api/alerts/subscriptions")
    assert resp.status_code == 200
    assert resp.json() == []
