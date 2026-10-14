"""Source for the recovered CdpDraftPage._call replacement. No external retry."""

def _call(self, method, params):
    import json
    import os
    import platform
    import time
    from datetime import datetime, timezone
    from pathlib import Path
    from uuid import uuid4
    from websocket import WebSocketTimeoutException

    started = time.monotonic()
    attempted = False
    safe_method = method if method in {
        'Runtime.evaluate', 'DOM.setFileInputFiles', 'DOM.getDocument',
        'DOM.querySelector', 'Input.insertText', 'Input.dispatchKeyEvent',
        'Input.dispatchMouseEvent', 'Page.bringToFront',
    } else 'other'

    def fail(code, phase, message, poison=True):
        if poison:
            self._xcl_failed = True
            try:
                self.socket.close()
            except Exception:
                pass
        error = XiaodouyaError(message + ' 未自动重试，请核对当前页面。', code=code)
        report = {
            'schema': 1, 'version': 'v0.5.44-r2',
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'operation': safe_method, 'phase': phase, 'cause_code': code,
            'send_attempted': attempted, 'elapsed_seconds': round(time.monotonic()-started, 3),
            'timeout_seconds': self.timeout, 'system': platform.system(),
            'release': platform.release(), 'machine': platform.machine(),
        }
        try:
            override = os.environ.get('XCL_PUBLISH_DATA_DIR')
            base = Path(override) if override else Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Xincailian' / 'PublishHelper'
            directory = base / 'diagnostics'
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / ('连接故障_' + uuid4().hex + '.json')
            with path.open('x', encoding='utf-8') as stream:
                json.dump(report, stream, ensure_ascii=False, indent=2)
            error.diagnostic_path = str(path.resolve())
            error.args = (str(error) + ' 诊断已保存：' + error.diagnostic_path,)
        except Exception:
            error.args = (str(error) + ' 诊断文件未能保存。',)
        return error

    if getattr(self, '_xcl_failed', False):
        raise fail('cdp_connection_unusable', 'before_send', '上次连接结果未知，已停止继续使用该连接。', False) from None
    self.sequence += 1
    command_id = self.sequence
    deadline = started + self.timeout
    # Serialize before sending so local encoding errors never masquerade as connection errors.
    encoded = json.dumps({'id': command_id, 'method': method, 'params': params})
    try:
        self.socket.settimeout(self.timeout)
        attempted = True
        self.socket.send(encoded)
    except (TimeoutError, WebSocketTimeoutException):
        raise fail('cdp_send_timeout', 'send', '向小豆芽发送指令超时，执行结果待核对。') from None
    except Exception:
        raise fail('cdp_disconnected', 'send', '向小豆芽发送指令时连接中断，执行结果待核对。') from None
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise fail('cdp_response_timeout', 'receive', '等待小豆芽指令响应超时，执行结果待核对。') from None
        try:
            self.socket.settimeout(remaining)
            raw = self.socket.recv()
        except (TimeoutError, WebSocketTimeoutException):
            raise fail('cdp_response_timeout', 'receive', '等待小豆芽指令响应超时，执行结果待核对。') from None
        except Exception:
            raise fail('cdp_disconnected', 'receive', '读取小豆芽响应时连接中断，执行结果待核对。') from None
        if raw in ('', b'', None):
            raise fail('cdp_disconnected', 'receive', '小豆芽连接已关闭，执行结果待核对。') from None
        try:
            message = json.loads(raw)
        except (ValueError, TypeError, UnicodeError):
            raise fail('cdp_invalid_response', 'decode', '小豆芽响应格式异常，已停止后续操作。') from None
        if not isinstance(message, dict):
            raise fail('cdp_invalid_response', 'decode', '小豆芽响应结构异常，已停止后续操作。') from None
        if message.get('id') != command_id:
            continue
        if 'error' in message:
            raise fail('cdp_command_rejected', 'response', '小豆芽页面拒绝本次指令，已停止后续操作。') from None
        if not isinstance(message.get('result'), dict):
            raise fail('cdp_invalid_response', 'response', '小豆芽指令结果格式异常，已停止后续操作。') from None
        return message['result']
