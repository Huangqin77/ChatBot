"""Runner safeguards and controlled fixtures. Never external-model evidence."""
import asyncio
import importlib.util
import json
from pathlib import Path

import httpx
import pytest
from sqlalchemy import inspect
from sqlmodel import Session, select

from app import llm
from app.config import Settings
from app.db import initialize, make_engine
from app.models import ToolCall
from app.tools import validate_tool_args

spec = importlib.util.spec_from_file_location('real_validation', Path(__file__).resolve().parents[2] / 'scripts/validate_real_llm.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_missing_credentials_never_calls_provider(tmp_path, monkeypatch):
    async def forbidden(*_):
        raise AssertionError('Must not call provider without credentials')
    monkeypatch.setattr(llm, 'complete', forbidden)
    report, code = asyncio.run(runner.validate(Settings(api_key=''), tmp_path))
    assert code == 2 and report['conclusion'] == 'C'
    assert set(report['checks'].values()) == {'NOT RUN'} and report['external_requests_attempted'] == 0


def test_request_budget_blocks_additional_requests():
    count = 0
    async def provider(*_):
        nonlocal count
        count += 1
        return {'role': 'assistant', 'content': 'OK'}
    async def scenario():
        audit = runner.RequestAudit(provider, 1)
        await audit.complete(Settings(), [], [])
        with pytest.raises(llm.ModelError, match='预算'):
            await audit.complete(Settings(), [], [])
    asyncio.run(scenario())
    assert count == 1


@pytest.mark.parametrize(('name', 'args'), [
    ('calculator', {'expression': 123}), ('calculator', {'expression': '1+1', 'shell': 'bad'}),
    ('delegate_to_bot', {'bot_name': 'x', 'task': 'job', 'extra': 'bad'}),
    ('delegate_to_bot', {'bot_name': ['x'], 'task': 'job'}),
    ('get_current_time', {}), ('get_current_time', {'timezone': ['UTC']})])
def test_schema_rejects_invalid_tool_arguments(name, args):
    with pytest.raises(ValueError, match='Schema'):
        validate_tool_args(name, args)


def test_legacy_database_gets_additive_migration(tmp_path):
    engine = make_engine('sqlite:///' + (tmp_path / 'legacy.db').as_posix())
    initialize(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql('ALTER TABLE tool_calls DROP COLUMN provider_call_id')
    assert 'provider_call_id' not in {c['name'] for c in inspect(engine).get_columns('tool_calls')}
    initialize(engine)
    initialize(engine)  # Idempotent on a current database.
    with Session(engine) as session:
        assert session.exec(select(ToolCall)).all() == []
    assert 'provider_call_id' in {c['name'] for c in inspect(engine).get_columns('tool_calls')}
    engine.dispose()


@pytest.mark.parametrize('use_tools', [True, False])
def test_runner_with_controlled_transport_is_not_real_evidence(tmp_path, monkeypatch, use_tools):
    """Exercises the actual temporary HTTP/WS server; only provider transport is a fixture."""
    def provider(req):
        body = json.loads(req.content)
        messages = body['messages']
        system = messages[0].get('content', '')
        results = [m for m in messages if m['role'] == 'tool']
        if not body.get('tools'):
            reply = {'role': 'assistant', 'content': 'OK'}
        elif not use_tools or results:
            reply = {'role': 'assistant', 'content': '受控测试结果 4608'}
        else:
            name = 'delegate_to_bot' if system.startswith('你是规划助手') else 'calculator'
            args = {'bot_name': '数据助手', 'task': '计算128*36'} if name == 'delegate_to_bot' else {'expression': '128*36'}
            # Reusing call-1 across independent Bot conversations is valid and must remain traceable.
            reply = {'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'call-1', 'type': 'function',
                'function': {'name': name, 'arguments': json.dumps(args, ensure_ascii=False)}}]}
        return httpx.Response(200, json={'choices': [{'message': reply}]})
    original_client = httpx.AsyncClient
    def client_factory(**kwargs):
        if 'base_url' not in kwargs:
            kwargs['transport'] = httpx.MockTransport(provider)
        return original_client(**kwargs)
    monkeypatch.setattr(llm.httpx, 'AsyncClient', client_factory)
    report, code = asyncio.run(runner.validate(Settings(api_key='fixture-only-not-a-real-key', base_url='https://fixture.invalid/v1'), tmp_path))
    # This report stays in memory, never exported as a real run or mixed into acceptance evidence.
    if use_tools:
        assert code == 0 and set(report['checks'].values()) == {'PASS'}
        assert report['external_requests_attempted'] == 7
        assert len(report['scenarios']) == 2
        assert all(c['provider_call_id'] == 'call-1' for s in report['scenarios'] for c in s['tool_calls'])
    else:
        assert code == 1 and report['checks']['calculator'] == 'FAIL'
        assert report['checks']['delegate_to_bot'] == 'NOT RUN'


def test_evidence_export_removes_credentials():
    evidence = {'token': 'local-session', 'nested': {'Authorization': 'Bearer x', 'text': 'private-value'}}
    assert runner.clean(evidence, 'private-value') == {'nested': {'text': '[REDACTED]'}}
