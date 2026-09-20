"""Run with pytest backend/test_support_images.py; no live DB or accounts used."""
import asyncio
import base64
from contextlib import contextmanager
import importlib.util
import io
from pathlib import Path
import sqlite3
import sys
import types

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin
from pydantic import BaseModel

from utils import support_images


def image_b64(fmt='PNG'):
    output = io.BytesIO()
    image = Image.new('RGB', (32, 24), 'red')
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text('private', 'GPS-or-script-metadata')
    image.save(output, format=fmt, pnginfo=metadata)
    return base64.b64encode(output.getvalue()).decode()


@pytest.mark.parametrize('fmt', ['JPEG', 'PNG'])
def test_rewrites_pixels_and_drops_metadata_and_appended_bytes(fmt):
    raw = base64.b64decode(image_b64(fmt)) + b'<script>bad()</script>'
    result = support_images.normalize_support_image(base64.b64encode(raw).decode())
    assert b'<script>' not in result
    assert b'GPS-or-script-metadata' not in result
    with Image.open(io.BytesIO(result)) as image:
        assert image.format == 'JPEG'
        assert image.size == (32, 24)
        assert not image.getexif()


@pytest.mark.parametrize('raw', [b'<svg onload="bad()"/>', b'%PDF-1.7', b'MZexe', b'\x89PNG\r\n\x1a\ntruncated', b''])
def test_rejects_non_images_and_broken_images(raw):
    with pytest.raises(HTTPException):
        support_images.normalize_support_image(base64.b64encode(raw).decode())


def test_rejects_invalid_base64_and_oversized_image():
    for encoded in ['not base64!', 'A' * (support_images.MAX_BASE64_LENGTH + 1)]:
        with pytest.raises(HTTPException):
            support_images.normalize_support_image(encoded)


def test_rejects_pixel_bombs_and_animation(monkeypatch):
    monkeypatch.setattr(support_images, 'MAX_IMAGE_PIXELS', 100)
    with pytest.raises(HTTPException):
        support_images.normalize_support_image(image_b64())
    monkeypatch.setattr(support_images, 'MAX_IMAGE_PIXELS', 12_000_000)
    output = io.BytesIO()
    Image.new('RGB', (10, 10), 'red').save(output, format='PNG', save_all=True,
                                        append_images=[Image.new('RGB', (10, 10), 'blue')])
    with pytest.raises(HTTPException):
        support_images.normalize_support_image(base64.b64encode(output.getvalue()).decode())


def test_chunked_body_limit():
    class Request:
        headers = {'content-type': 'application/json'}

        async def stream(self):
            for _ in range(8):
                yield b'x' * (1024 * 1024)

    with pytest.raises(HTTPException) as error:
        asyncio.run(support_images.read_support_json(Request()))
    assert error.value.status_code == 413


def test_decode_concurrency_is_bounded():
    support_images._DECODE_SLOTS.acquire()
    support_images._DECODE_SLOTS.acquire()
    try:
        with pytest.raises(HTTPException) as error:
            support_images.normalize_support_image(image_b64())
        assert error.value.status_code == 429
    finally:
        support_images._DECODE_SLOTS.release()
        support_images._DECODE_SLOTS.release()


@pytest.fixture
def support_app(tmp_path, monkeypatch):
    # Stub only external services; exercise the actual routes and SQL transactions.
    class User(BaseModel):
        userid: int
        role: str = 'user'

    identity = {'user': User(userid=1)}

    def current_user():
        if identity['user'] is None:
            raise HTTPException(401, 'Login required')
        return identity['user']

    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.executescript('''
        CREATE TABLE support_tickets (id INTEGER PRIMARY KEY, userid INTEGER, subject TEXT,
          status TEXT, source TEXT, last_message_preview TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP);
        CREATE TABLE support_messages (id INTEGER PRIMARY KEY, ticket_id INTEGER,
          author_role TEXT, author_userid INTEGER, body TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE support_message_attachments (id INTEGER PRIMARY KEY, ticket_id INTEGER,
          message_id INTEGER, filename TEXT, mime_type TEXT, storage_path TEXT, size_bytes INTEGER,
          uploaded_by_role TEXT, uploaded_by_userid INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    ''')

    @contextmanager
    def get_conn():
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise

    def execute(connection, sql, params=()):
        if 'pg_advisory_xact_lock' in sql:
            return connection.execute('SELECT 1')
        sql = sql.replace('%s', '?').replace("CURRENT_TIMESTAMP - INTERVAL '1 hour'", "datetime('now', '-1 hour')")
        sql = sql.replace("CURRENT_TIMESTAMP - INTERVAL '24 hours'", "datetime('now', '-24 hours')")
        return connection.execute(sql, params)

    for name, attributes in {
        'auth': {'User': User, 'get_current_user': current_user},
        'db': {'get_conn': get_conn, 'execute': execute},
        'utils.smtp_mail': {'send_plain_text_email': lambda *a, **k: None},
    }.items():
        stub = types.ModuleType(name)
        stub.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, stub)
    spec = importlib.util.spec_from_file_location('support_routes_under_test', Path(__file__).with_name('support_routes.py'))
    routes = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, routes)
    spec.loader.exec_module(routes)
    routes._TICKETS_TABLE_READY = True
    routes.SUPPORT_ATTACHMENT_DIR = tmp_path
    routes._fetch_user_contact = lambda *a: (None, 'Test', None)
    routes._notify_help_staff_new_ticket = lambda *a: None
    routes._notify_help_staff_user_reply = lambda *a: None
    app = FastAPI()
    app.include_router(routes.router, prefix='/support')
    with TestClient(app) as client:
        yield client, conn, identity, User, routes
    conn.close()


def test_create_reply_and_private_download(support_app):
    client, conn, identity, User, routes = support_app
    created = client.post('/support/tickets', json={'subject': 'Bug', 'message': 'Screenshot', 'image_base64': image_b64()})
    assert created.status_code == 200
    ticket_id = created.json()['ticket_id']
    assert client.post(f'/support/tickets/{ticket_id}/messages', json={'message': 'More detail', 'image_base64': image_b64('JPEG')}).status_code == 200
    rows = conn.execute('SELECT id, filename, mime_type, uploaded_by_role FROM support_message_attachments').fetchall()
    assert len(rows) == 2
    assert rows[0][1:] == ('support-image.jpg', 'image/jpeg', 'user')
    url = f'/support/attachments/{rows[0][0]}/download'
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['cache-control'] == 'private, no-store'
    assert response.headers['content-disposition'].startswith('attachment;')
    identity['user'] = User(userid=2)
    assert client.get(url).status_code == 403
    assert client.post(f'/support/tickets/{ticket_id}/messages', json={'message': 'Attack', 'image_base64': image_b64()}).status_code == 403
    assert len(list(routes.SUPPORT_ATTACHMENT_DIR.iterdir())) == 2
    identity['user'] = User(userid=2, role='admin')
    assert client.get(url).status_code == 200
    identity['user'] = None
    assert client.get(url).status_code == 401
    assert client.post('/support/tickets', json={'subject': 'Bug', 'message': 'Test', 'image_base64': image_b64()}).status_code == 401


def test_invalid_image_does_not_create_ticket_and_text_only_still_works(support_app):
    client, conn, _, _, routes = support_app
    assert client.post('/support/tickets', json={'subject': 'Bug', 'message': 'Test', 'image_base64': 'invalid'}).status_code == 400
    assert conn.execute('SELECT COUNT(*) FROM support_tickets').fetchone()[0] == 0
    assert not list(routes.SUPPORT_ATTACHMENT_DIR.iterdir())
    assert client.post('/support/tickets', json={'subject': 'Bug', 'message': 'Test'}).status_code == 200


def test_closed_ticket_and_rate_limit(support_app):
    client, conn, _, _, routes = support_app
    for _ in range(5):
        assert client.post('/support/tickets', json={'subject': 'Bug', 'message': 'Test'}).status_code == 200
    assert client.post('/support/tickets', json={'subject': 'Bug', 'message': 'Test', 'image_base64': image_b64()}).status_code == 429
    conn.execute("UPDATE support_tickets SET status='closed' WHERE id=1")
    conn.commit()
    assert client.post('/support/tickets/1/messages', json={'message': 'Test', 'image_base64': image_b64()}).status_code == 400
    assert not list(routes.SUPPORT_ATTACHMENT_DIR.iterdir())


def test_failed_database_insert_removes_file(support_app, monkeypatch):
    client, conn, _, _, routes = support_app
    original = routes.execute

    def fail_insert(connection, sql, params=()):
        if 'INSERT INTO support_message_attachments' in sql:
            raise RuntimeError('Simulated database failure')
        return original(connection, sql, params)

    monkeypatch.setattr(routes, 'execute', fail_insert)
    with pytest.raises(RuntimeError, match='Simulated database failure'):
        client.post('/support/tickets', json={'subject': 'Bug', 'message': 'Test', 'image_base64': image_b64()})
    assert conn.execute('SELECT COUNT(*) FROM support_tickets').fetchone()[0] == 0
    assert not list(routes.SUPPORT_ATTACHMENT_DIR.iterdir())


def test_image_quota_does_not_block_text_replies(support_app, monkeypatch):
    client, _, _, _, routes = support_app
    monkeypatch.setattr(routes, 'SUPPORT_USER_IMAGES_PER_DAY', 1)
    assert client.post('/support/tickets', json={'subject': 'Bug', 'message': 'Test', 'image_base64': image_b64()}).status_code == 200
    assert client.post('/support/tickets/1/messages', json={'message': 'Test', 'image_base64': image_b64()}).status_code == 429
    assert client.post('/support/tickets/1/messages', json={'message': 'Text reply'}).status_code == 200


def test_storage_quota_and_download_path_boundary(support_app, monkeypatch, tmp_path):
    client, conn, _, _, routes = support_app
    monkeypatch.setattr(routes, 'SUPPORT_USER_IMAGE_STORAGE_BYTES', 1)
    assert client.post('/support/tickets', json={'subject': 'Bug', 'message': 'Test', 'image_base64': image_b64()}).status_code == 429
    monkeypatch.setattr(routes, 'SUPPORT_USER_IMAGE_STORAGE_BYTES', 50 * 1024 * 1024)
    assert client.post('/support/tickets', json={'subject': 'Bug', 'message': 'Test', 'image_base64': image_b64()}).status_code == 200
    conn.execute('UPDATE support_message_attachments SET storage_path=?', (str(tmp_path.parent / 'outside.jpg'),))
    conn.commit()
    assert client.get('/support/attachments/1/download').status_code == 404
