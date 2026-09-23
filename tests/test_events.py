"""
Unit tests for SHIVANI Event System.
"""

import asyncio
import pytest
from core.events.bus import EventBus, EventType, Event


def test_event_bus_publish_and_subscribe():
    bus = EventBus()
    received = []

    def on_event(e: Event):
        received.append(e)

    bus.subscribe(on_event)
    event = bus.publish(EventType.TASK_CREATED, task_id="t101", data={"query": "test"})

    assert len(received) == 1
    assert received[0].id == event.id
    assert received[0].event_type == EventType.TASK_CREATED
    assert received[0].task_id == "t101"
    assert received[0].data["query"] == "test"

    # History verification
    history = bus.get_history()
    assert len(history) == 1
    assert history[0].task_id == "t101"


@pytest.mark.asyncio
async def test_event_bus_queue_streaming():
    bus = EventBus()
    queue = bus.create_subscription_queue()

    bus.publish(EventType.TASK_STARTED, task_id="t202", data={"steps": 3})
    event = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert event.event_type == EventType.TASK_STARTED
    assert event.task_id == "t202"

    bus.remove_subscription_queue(queue)
