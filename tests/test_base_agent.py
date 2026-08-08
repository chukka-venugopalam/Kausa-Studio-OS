"""Unit test for the retry-safety contract every agent depends on:
a run always writes 'running' then 'success' or 'failed' -- never
neither. Uses a mocked Supabase client, so this runs with no network
and no real credentials, in CI or locally.
"""
from unittest.mock import MagicMock, patch

import pytest

from agents.base_agent import BaseAgent


class DummyAgent(BaseAgent):
    name = "dummy_agent"

    def execute(self, should_fail: bool = False):
        if should_fail:
            raise ValueError("boom")
        return {"ok": True}


def _mock_db():
    db = MagicMock()
    insert_result = MagicMock()
    insert_result.data = [{"id": "run-123"}]
    db.table.return_value.insert.return_value.execute.return_value = insert_result
    return db


@patch("agents.base_agent.get_client")
def test_successful_run_writes_success_status(mock_get_client):
    mock_get_client.return_value = _mock_db()
    agent = DummyAgent(brand_id="brand-1")

    result = agent.run(should_fail=False)

    assert result == {"ok": True}
    update_call = agent.db.table.return_value.update.call_args[0][0]
    assert update_call["status"] == "success"
    assert update_call["error_message"] is None


@patch("agents.base_agent.get_client")
def test_failed_run_writes_failed_status_and_reraises(mock_get_client):
    mock_get_client.return_value = _mock_db()
    agent = DummyAgent(brand_id="brand-1")

    with pytest.raises(ValueError):
        agent.run(should_fail=True)

    update_call = agent.db.table.return_value.update.call_args[0][0]
    assert update_call["status"] == "failed"
    assert "boom" in update_call["error_message"]
