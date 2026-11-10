import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(Settings(database_url='sqlite:///' + (tmp_path / 'test.db').as_posix(), mode='demo', api_key=''))


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def identity(client):
    user = client.post('/api/users', json={'nickname': '测试用户'}).json()
    return user, {'Authorization': 'Bearer ' + user['token']}


def receive_until(ws, predicate, maximum=80):
    for _ in range(maximum):
        event = ws.receive_json()
        if predicate(event):
            return event
    raise AssertionError('Expected WebSocket event not received')


def send(ws, content, client_id):
    ws.send_json({'type': 'message', 'content': content, 'client_id': client_id})
