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
        # Task progress messages (graph build)
        'init_graph_service': '初始化图谱构建服务...',
        'text_chunking': '文本分块中...',
        'creating_zep_graph': '创建Zep图谱...',
        'setting_ontology': '设置本体定义...',
        'adding_text_chunks': '开始添加 {count} 个文本块...',
        'waiting_zep': '等待Zep处理数据...',
        'fetching_graph_data': '获取图谱数据...',
        'graph_build_complete': '图谱构建完成',
        'build_failed': '构建失败: {error}',
        'graph_build_started': '图谱构建任务已启动，请通过 /task/{task_id} 查询进度',
        # graph_builder.py messages
        'building_graph': '开始构建图谱...',
        'graph_created': '图谱已创建: {graph_id}',
        'ontology_set': '本体已设置',
        'text_split': '文本已分割为 {count} 个块',
        'fetching_graph_info': '获取图谱信息...',
        'sending_batch': '发送第 {current}/{total} 批数据 ({chunks} 块)...',
        'batch_failed': '批次 {batch} 发送失败: {error}',
        'no_episodes': '无需等待（没有 episode）',
        'waiting_episodes': '开始等待 {count} 个文本块处理...',
        'episodes_timeout': '部分文本块超时，已完成 {done}/{total}',
        'zep_processing': 'Zep处理中... {done}/{total} 完成, {pending} 待处理 ({elapsed}秒)',
        'processing_done': '处理完成: {done}/{total}',
    },
    'en': {
        'missing_simulation_id': 'Please provide simulation_id',
        'missing_message': 'Please provide message',
        'simulation_not_found': 'Simulation not found',
        'project_not_found': 'Project not found',
        'missing_graph_id': 'Missing graph ID',
        # Task progress messages (graph build)
        'init_graph_service': 'Initializing graph build service...',
        'text_chunking': 'Chunking text...',
        'creating_zep_graph': 'Creating Zep graph...',
        'setting_ontology': 'Setting ontology definition...',
        'adding_text_chunks': 'Adding {count} text chunks...',
        'waiting_zep': 'Waiting for Zep to process data...',
        'fetching_graph_data': 'Fetching graph data...',
        'graph_build_complete': 'Graph build complete',
        'build_failed': 'Build failed: {error}',
        'graph_build_started': 'Graph build task started. Check progress via /task/{task_id}',
        # graph_builder.py messages
        'building_graph': 'Starting graph build...',
        'graph_created': 'Graph created: {graph_id}',
        'ontology_set': 'Ontology set',
        'text_split': 'Text split into {count} chunks',
        'fetching_graph_info': 'Fetching graph info...',
        'sending_batch': 'Sending batch {current}/{total} ({chunks} chunks)...',
        'batch_failed': 'Batch {batch} failed: {error}',
        'no_episodes': 'No waiting needed (no episodes)',
        'waiting_episodes': 'Waiting for {count} text chunks to process...',
        'episodes_timeout': 'Some chunks timed out. Completed {done}/{total}',
        'zep_processing': 'Zep processing... {done}/{total} done, {pending} pending ({elapsed}s)',
        'processing_done': 'Processing done: {done}/{total}',
    },
    'ko': {
        'missing_simulation_id': 'simulation_id를 입력하세요',
        'missing_message': 'message를 입력하세요',
        'simulation_not_found': '시뮬레이션을 찾을 수 없습니다',
        'project_not_found': '프로젝트를 찾을 수 없습니다',
        'missing_graph_id': '그래프 ID가 누락되었습니다',
        # Task progress messages (graph build)
        'init_graph_service': '그래프 구축 서비스 초기화 중...',
        'text_chunking': '텍스트 분할 중...',
        'creating_zep_graph': 'Zep 그래프 생성 중...',
        'setting_ontology': '온톨로지 정의 설정 중...',
        'adding_text_chunks': '{count}개 텍스트 청크 추가 중...',
        'waiting_zep': 'Zep 데이터 처리 대기 중...',
        'fetching_graph_data': '그래프 데이터 가져오는 중...',
        'graph_build_complete': '그래프 구축 완료',
        'build_failed': '구축 실패: {error}',
        'graph_build_started': '그래프 구축 작업이 시작되었습니다. /task/{task_id}로 진행 상황을 확인하세요',
        # graph_builder.py messages
        'building_graph': '그래프 구축 시작...',
        'graph_created': '그래프 생성됨: {graph_id}',
        'ontology_set': '온톨로지 설정 완료',
        'text_split': '텍스트가 {count}개 청크로 분할됨',
        'fetching_graph_info': '그래프 정보 가져오는 중...',
        'sending_batch': '배치 {current}/{total} 전송 중 ({chunks}개 청크)...',
        'batch_failed': '배치 {batch} 전송 실패: {error}',
        'no_episodes': '대기 불필요 (에피소드 없음)',
        'waiting_episodes': '{count}개 텍스트 청크 처리 대기 중...',
        'episodes_timeout': '일부 청크 시간 초과. {done}/{total} 완료',
        'zep_processing': 'Zep 처리 중... {done}/{total} 완료, {pending} 대기 ({elapsed}초)',
        'processing_done': '처리 완료: {done}/{total}',
    },
}


def get_error_message(key: str, locale: str = 'zh') -> str:
    """Return localized error message. Fallback to zh if key missing for locale."""
    lang = locale if locale in MESSAGES else 'zh'
    return MESSAGES.get(lang, MESSAGES['zh']).get(key, MESSAGES['zh'].get(key, str(key)))
