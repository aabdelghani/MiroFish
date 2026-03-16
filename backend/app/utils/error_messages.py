"""
Error messages in zh/en for API responses.
"""

MESSAGES = {
    'zh': {
        'missing_simulation_id': '请提供 simulation_id',
        'missing_message': '请提供 message',
        'simulation_not_found': '模拟不存在',
        'project_not_found': '项目不存在',
        'missing_graph_id': '缺少图谱ID',
    },
    'en': {
        'missing_simulation_id': 'Please provide simulation_id',
        'missing_message': 'Please provide message',
        'simulation_not_found': 'Simulation not found',
        'project_not_found': 'Project not found',
        'missing_graph_id': 'Missing graph ID',
    },
    'ko': {
        'missing_simulation_id': 'simulation_id를 입력하세요',
        'missing_message': 'message를 입력하세요',
        'simulation_not_found': '시뮬레이션을 찾을 수 없습니다',
        'project_not_found': '프로젝트를 찾을 수 없습니다',
        'missing_graph_id': '그래프 ID가 누락되었습니다',
    },
}


def get_error_message(key: str, locale: str = 'zh') -> str:
    """Return localized error message. Fallback to zh if key missing for locale."""
    lang = locale if locale in MESSAGES else 'zh'
    return MESSAGES.get(lang, MESSAGES['zh']).get(key, MESSAGES['zh'].get(key, str(key)))
