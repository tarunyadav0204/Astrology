from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
import sms_service as module


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setenv('MTALKZ_API_KEY', 'test-secret')
    monkeypatch.setenv('MTALKZ_SENDER_ID', 'ASTROS')
    monkeypatch.setenv('MTALKZ_TEMPLATE_ID', 'template-123')
    monkeypatch.setenv('MTALKZ_OTP_MESSAGE', 'Your AstroRoshni OTP is {otp}.')
    monkeypatch.setenv('MTALKZ_PE_ID', 'entity-123')
    monkeypatch.setenv('SMS_PROVIDER', 'auto')
    monkeypatch.setattr(module, 'Client', Mock())
    return module.SMSService()


def response(body, status=200):
    return SimpleNamespace(status_code=status, json=lambda: body)


def test_primary_payload_and_no_fallback(service, monkeypatch, capsys):
    post = Mock(return_value=response({'status': 'OK', 'data': [
        {'id': 'request-1', 'mobile': '919876543210', 'status': 'SUBMITTED'}]}))
    monkeypatch.setattr(module.requests, 'post', post)
    service._send_via_msg91 = Mock()
    service._send_via_twilio = Mock()
    assert service.send_reset_code('+91 98765 43210', '012345') is True
    assert post.call_args.kwargs['json'] == {
        'apikey': 'test-secret', 'senderid': 'ASTROS', 'number': '919876543210',
        'message': 'Your AstroRoshni OTP is 012345.', 'template_id': 'template-123',
        'pe_id': 'entity-123', 'format': 'json'}
    assert post.call_args.kwargs['timeout'] == (3, 8)
    service._send_via_msg91.assert_not_called()
    service._send_via_twilio.assert_not_called()
    logs = capsys.readouterr().out
    assert 'SMS OTP request accepted - provider=mtalkz' in logs
    assert '012345' not in logs
    assert 'test-secret' not in logs


@pytest.mark.parametrize('body,status', [
    ({'status': 'AZQ02', 'message': 'Invalid API key'}, 200),
    ({'status': 'OK', 'data': [{'id': '1', 'mobile': '919876543210', 'status': 'FAILED'}]}, 200),
    ({'status': 'OK', 'data': []}, 200),
    ({'status': 'OK', 'data': [{'id': '1', 'mobile': '919999999999', 'status': 'SUBMITTED'}]}, 200),
    ([], 200), ({'status': 'OK'}, 503),
])
def test_rejected_requests_fall_back(service, monkeypatch, body, status):
    monkeypatch.setattr(module.requests, 'post', Mock(return_value=response(body, status)))
    service._send_via_msg91 = Mock(return_value=True)
    service._send_via_twilio = Mock()
    assert service.send_reset_code('9876543210', '123456') is True
    service._send_via_msg91.assert_called_once_with('9876543210', '123456')
    service._send_via_twilio.assert_not_called()


@pytest.mark.parametrize('error', [requests.Timeout('test-secret'), ValueError('invalid JSON')])
def test_exception_fallback_without_secret_logging(service, monkeypatch, capsys, error):
    monkeypatch.setattr(module.requests, 'post', Mock(side_effect=error))
    service._send_via_msg91 = Mock(return_value=False)
    service._send_via_twilio = Mock(return_value=True)
    assert service.send_reset_code('9876543210', '123456')
    service._send_via_twilio.assert_called_once()
    assert 'test-secret' not in capsys.readouterr().out


def test_incomplete_config_uses_existing_provider(service, monkeypatch, capsys):
    service.mtalkz_sender_id = ''
    post = Mock()
    monkeypatch.setattr(module.requests, 'post', post)
    service.provider = 'msg91'
    service._send_via_msg91 = Mock(return_value=True)
    assert service.send_reset_code('9876543210', '123456')
    post.assert_not_called()
    assert 'SMS OTP request accepted - provider=msg91' in capsys.readouterr().out


def test_international_skips_domestic_primary(service, monkeypatch):
    post = Mock()
    monkeypatch.setattr(module.requests, 'post', post)
    service._send_via_twilio = Mock(return_value=True)
    assert service.send_reset_code('+14155552671', '123456')
    assert not service._is_india_number('+1234567890')
    assert not service._is_india_number('+91987654321099')
    post.assert_not_called()


def test_all_providers_fail(service):
    service._send_via_mtalkz = Mock(return_value=False)
    service._send_via_msg91 = Mock(return_value=False)
    service._send_via_twilio = Mock(return_value=False)
    assert service.send_reset_code('9876543210', '123456') is False


def test_msg91_error_message_is_not_accepted(service, monkeypatch):
    service.msg91_auth_key = 'fallback-key'
    service.msg91_template_id = 'fallback-template'
    r = response({'type': 'error', 'message': 'Invalid template'})
    r.headers = {'content-type': 'application/json'}
    r.text = 'error'
    monkeypatch.setattr(module.requests, 'post', Mock(return_value=r))
    assert service._send_via_msg91('9876543210', '123456') is False
