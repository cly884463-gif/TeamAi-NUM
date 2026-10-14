"""Account enumeration: bounded complete passes, independent verification budget."""

def list_logged_accounts(platform, timeout=60):
    import os
    from pathlib import Path
    from datetime import datetime, timezone
    from uuid import uuid4

    started = time.monotonic()
    rounds = []
    stage = 'select_main_page'
    try:
        if platform not in PLATFORM_LABELS:
            raise XiaodouyaError('目标平台无效，无法读取账号。', code='invalid_account_binding')
        if not isinstance(timeout, (int, float)) or not 0 < timeout <= 60:
            raise XiaodouyaError('账号读取时间设置无效。', code='account_list_unavailable')
        target = _select_main_page(_targets())
        with _open(target) as main:
            stage = 'clear_filter'
            _clear_search_filter(main, min(timeout, 3), required=True)
            previous = None
            # A completed first pass cannot spend the second pass's budget.
            # Only complete successful scans can initiate another pass.
            # A transport error/partial inventory exits immediately, without retry.
            for index in range(3):
                stage = 'inventory' if index == 0 else 'verification'
                begin = time.monotonic()
                item = {'pass': index + 1, 'completed': False}
                rounds.append(item)
                try:
                    accounts, ambiguous = _scan_account_inventory(
                        main, PLATFORM_LABELS[platform], begin + timeout)
                finally:
                    item['elapsed_seconds'] = round(time.monotonic() - begin, 3)
                    item['scan'] = dict(getattr(main, '_xcl_inventory_progress', {}))
                item['completed'] = True
                if not isinstance(accounts, tuple) or not all(isinstance(x, str) and x.strip() for x in accounts):
                    raise XiaodouyaError('小豆芽账号列表读取失败，未返回部分结果。', code='account_list_unavailable')
                item['account_count'] = len(accounts)
                item['ambiguous_count'] = len(ambiguous)
                if ambiguous:
                    raise XiaodouyaError('小豆芽中存在重复的完整账号名称，无法安全区分，请修改显示名后重新读取。', code='target_account_ambiguous')
                if accounts == previous:
                    if not accounts:
                        raise XiaodouyaError('小豆芽中没有可用的' + PLATFORM_LABELS[platform] + '账号，请先登录账号。', code='target_account_missing')
                    return accounts
                previous = accounts
                if index < 2:
                    time.sleep(.25)
            raise XiaodouyaError('小豆芽账号列表连续三轮仍不一致，已停止读取，未返回部分账号。', code='account_list_unstable')
    except Exception as error:
        # Diagnostic data contains counts and stages only, never names/IDs/URLs.
        report = {'schema': 1, 'version': 'v0.5.44-r13',
                  'checked_at': datetime.now(timezone.utc).isoformat(),
                  'operation_stage': 'account_inventory', 'phase': stage,
                  'cause_code': getattr(error, 'code', 'unexpected_error'),
                  'elapsed_seconds': round(time.monotonic() - started, 3),
                  'rounds': rounds, 'partial_results_returned': False}
        try:
            override = os.environ.get('XCL_PUBLISH_DATA_DIR')
            base = Path(override) if override else Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Xincailian' / 'PublishHelper'
            directory = base / 'diagnostics'
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / ('账号读取诊断_' + uuid4().hex + '.json')
            with path.open('x', encoding='utf-8') as stream:
                json.dump(report, stream, ensure_ascii=False, indent=2)
            # Keep an existing transport diagnostic too.
            error.args = (str(error) + ' 账号诊断已保存：' + str(path.resolve()),)
        except Exception:
            pass
        raise
