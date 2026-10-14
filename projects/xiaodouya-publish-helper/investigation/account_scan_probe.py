def _scan_account_inventory(main, platform_label, deadline):
    def original(main, platform_label, deadline):
        pass
    stats = {'steps': 0, 'waiting_steps': 0}
    main._xcl_inventory_progress = stats
    class Probe:
        def _evaluate(self, expression):
            result = main._evaluate(expression)
            if isinstance(result, dict) and isinstance(result.get('rows'), list):
                stats['steps'] += 1
                stats['waiting_steps'] += int(result.get('waiting') is True)
                stats['last_rows'] = len(result['rows'])
                stats['last_done'] = result.get('done') is True
                for key in ('top', 'max', 'pendingCount', 'loadingCount'):
                    value = result.get(key, 0 if key in ('pendingCount', 'loadingCount') else None)
                    if isinstance(value, (int, float)):
                        stats[key] = value
            return result
    return original(Probe(), platform_label, deadline)
