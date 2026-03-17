"""
Report API routes.
Provides simulation report generation, retrieval, and chat endpoints.

Provides endpoints for report generation, retrieval, and chat.
"""

import os
import threading
from flask import request, jsonify, send_file

from . import report_bp
from ..utils.request_locale import get_request_locale
from ..utils.error_messages import get_error_message
from ..services.report_agent import ReportAgent, ReportManager, ReportStatus
from ..services.simulation_manager import SimulationManager
from ..models.project import ProjectManager
from ..models.task import TaskManager, TaskStatus
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.report')


# ============== Report generation ==============
# ============== Report generation endpoints ==============

@report_bp.route('/generate', methods=['POST'])
def generate_report():
    """
    Generate simulation report (async).

    Returns task_id immediately; query progress via GET /api/report/generate/status.

    Request (JSON):
        simulation_id (required), force_regenerate (optional).

    Generate a simulation analysis report asynchronously.
    
    This is a long-running operation. The endpoint returns a task_id
    immediately, and progress can be checked via
    GET /api/report/generate/status.
    
    Generate a simulation analysis report asynchronously.

    This is a long-running operation. The endpoint returns a task_id
    immediately, and progress can be checked via
    GET /api/report/generate/status.

    Request (JSON):
        {
            "simulation_id": "sim_xxxx",    // required
            "force_regenerate": false        // optional, force regeneration
        }
    

    Returns:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "task_id": "task_xxxx",
                "status": "generating",
                "message": "Report generation task started"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        locale = get_request_locale()

        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id is required"
                "error": "Please provide simulation_id"
            }), 400

        force_regenerate = data.get('force_regenerate', False)
        

        # Load the simulation.
                "error": get_error_message('report_missing_sim_id', locale)
            }), 400

        force_regenerate = data.get('force_regenerate', False)

        # 获取模拟信息
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulation not found: {simulation_id}"
            }), 404
        

        # Reuse an existing completed report unless forced to regenerate.
                "error": get_error_message('report_sim_not_found', locale).format(simulation_id=simulation_id)
            }), 404

        # 检查是否已有报告
        if not force_regenerate:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "report_id": existing_report.report_id,
                        "status": "completed",
                        "message": "Report already exists",
                        "already_generated": True
                    }
                })
        

        # Load the project.
                        "message": get_error_message('report_already_exists', locale),
                        "already_generated": True
                    }
                })

        # 获取项目信息
        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Project not found: {state.project_id}"
                "error": get_error_message('report_project_not_found', locale).format(project_id=state.project_id)
            }), 404

        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "Graph ID is missing; ensure the graph has been built"
                "error": "Missing graph_id. Make sure the graph has been built."
                "error": get_error_message('report_missing_graph', locale)
            }), 400

        simulation_requirement = project.simulation_requirement
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "Simulation requirement description is missing"
            }), 400
        
                "error": get_error_message('report_missing_requirement', locale)
            }), 400
        
        # 获取用户语言偏好（在启动线程前捕获，线程内 request 可能不可用）
        report_language = locale
        
        # 提前生成 report_id，以便立即返回给前端
        import uuid
        report_id = f"report_{uuid.uuid4().hex[:12]}"
        
                "error": "Missing simulation requirement"
            }), 400
        
        # Generate report_id up front so the frontend gets it immediately.
        import uuid
        report_id = f"report_{uuid.uuid4().hex[:12]}"
        
                "error": "Missing simulation requirement"
            }), 400

        # Generate report_id up front so the frontend gets it immediately.
        import uuid
        report_id = f"report_{uuid.uuid4().hex[:12]}"

        # Create the async task.
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="report_generate",
            metadata={
                "simulation_id": simulation_id,
                "graph_id": graph_id,
                "report_id": report_id
            }
        )
        

        # Background task definition.
        def run_generate():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=0,
                    message="Initializing Report Agent..."
                )
                
                    message="Initializing report agent..."
                )
                
                    message="Initializing report agent..."
                )

                # Create the report agent.
                    message=get_error_message('report_init_agent', report_language)
                )
                
                # 创建Report Agent（传入用户语言，报告和对话均使用该语言）
                agent = ReportAgent(
                    graph_id=graph_id,
                    simulation_id=simulation_id,
                    simulation_requirement=simulation_requirement,
                    report_language=report_language
                )
                

                # Progress callback.
                def progress_callback(stage, progress, message):
                    task_manager.update_task(
                        task_id,
                        progress=progress,
                        message=f"[{stage}] {message}"
                    )
                

                # Generate the report using the pre-generated report_id.
                report = agent.generate_report(
                    progress_callback=progress_callback,
                    report_id=report_id
                )
                

                # Save the report.
                ReportManager.save_report(report)

                if report.status == ReportStatus.COMPLETED:
                    task_manager.complete_task(
                        task_id,
                        result={
                            "report_id": report.report_id,
                            "simulation_id": simulation_id,
                            "status": "completed"
                        }
                    )
                else:
                    task_manager.fail_task(task_id, report.error or "Report generation failed")
                
                    task_manager.fail_task(task_id, report.error or get_error_message('report_gen_failed', report_language))

            except Exception as e:
                logger.error(f"Report generation failed: {str(e)}")
                task_manager.fail_task(task_id, str(e))
        

            except Exception as e:
                logger.error(f"Report generation failed: {str(e)}")
                task_manager.fail_task(task_id, str(e))

        # Start the background thread.
        thread = threading.Thread(target=run_generate, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "report_id": report_id,
                "task_id": task_id,
                "status": "generating",
                "message": "Report generation task started; query progress via /api/report/generate/status",
                "message": "Report generation started. Query progress via /api/report/generate/status.",
                "message": get_error_message('report_gen_started', locale),
                "already_generated": False
            }
        })

    except Exception as e:
        logger.error(f"Failed to start report generation task: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/generate/status', methods=['POST'])
def get_generate_status():
    """
    Query report generation task progress.

    Request (JSON): task_id (optional), simulation_id (optional).

    Query report generation progress.
    
    Query report generation progress.

    Request (JSON):
        {
            "task_id": "task_xxxx",         // optional, task_id returned by generate
            "simulation_id": "sim_xxxx"     // optional
        }
    

    Returns:
        {
            "success": true,
            "data": {
                "task_id": "task_xxxx",
                "status": "processing|completed|failed",
                "progress": 45,
                "message": "..."
            }
        }
    """
    try:
        locale = get_request_locale()
        data = request.get_json() or {}

        task_id = data.get('task_id')
        simulation_id = data.get('simulation_id')
        

        # If simulation_id is provided, first check whether the report is already done.

        # 如果提供了simulation_id，先检查是否已有完成的报告
        if simulation_id:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "report_id": existing_report.report_id,
                        "status": "completed",
                        "progress": 100,
                        "message": "Report generated",
                        "message": "Report already generated",
                        "message": get_error_message('report_already_generated', locale),
                        "already_completed": True
                    }
                })

        if not task_id:
            return jsonify({
                "success": False,
                "error": "task_id or simulation_id is required"
                "error": "Please provide task_id or simulation_id"
                "error": get_error_message('report_missing_task_or_sim_id', locale)
            }), 400

        task_manager = TaskManager()
        task = task_manager.get_task(task_id)

        if not task:
            return jsonify({
                "success": False,
                "error": f"Task not found: {task_id}"
                "error": get_error_message('report_task_not_found', locale).format(task_id=task_id)
            }), 404

        return jsonify({
            "success": True,
            "data": task.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        logger.error(f"Failed to query task status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Report retrieval ==============
# ============== Report retrieval endpoints ==============

@report_bp.route('/<report_id>', methods=['GET'])
def get_report(report_id: str):
    """
    Get report details.

    
    Returns:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "simulation_id": "sim_xxxx",
                "status": "completed",
                "outline": {...},
                "markdown_content": "...",
                "created_at": "...",
                "completed_at": "..."
            }
        }
    """
    try:
        report = ReportManager.get_report(report_id)

        if not report:
            locale = get_request_locale()
            return jsonify({
                "success": False,
                "error": f"Report not found: {report_id}"
                "error": get_error_message('report_not_found', locale).format(report_id=report_id)
            }), 404

        return jsonify({
            "success": True,
            "data": report.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to get report: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/by-simulation/<simulation_id>', methods=['GET'])
def get_report_by_simulation(simulation_id: str):
    """
    Get report by simulation ID.

    Get a report by simulation ID.
    
    Get a report by simulation ID.

    Returns:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                ...
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)

        if not report:
            locale = get_request_locale()
            return jsonify({
                "success": False,
                "error": f"No report for this simulation: {simulation_id}",
                "error": f"No report exists for simulation: {simulation_id}",
                "error": get_error_message('report_no_report_for_sim', locale).format(simulation_id=simulation_id),
                "has_report": False
            }), 404

        return jsonify({
            "success": True,
            "data": report.to_dict(),
            "has_report": True
        })

    except Exception as e:
        logger.error(f"Failed to get report: {str(e)}")
        logger.error(f"Failed to get report by simulation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/list', methods=['GET'])
def list_reports():
    """
    List all reports.

    Query: simulation_id (optional), limit (default 50).

    List reports.
    
    Query parameters:
        simulation_id: filter by simulation ID (optional)
        limit: max number of results (default 50)
    
    List reports.

    Query parameters:
        simulation_id: filter by simulation ID (optional)
        limit: max number of results (default 50)

    Returns:
        {
            "success": true,
            "data": [...],
            "count": 10
        }
    """
    try:
        simulation_id = request.args.get('simulation_id')
        limit = request.args.get('limit', 50, type=int)

        reports = ReportManager.list_reports(
            simulation_id=simulation_id,
            limit=limit
        )

        return jsonify({
            "success": True,
            "data": [r.to_dict() for r in reports],
            "count": len(reports)
        })

    except Exception as e:
        logger.error(f"Failed to list reports: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/download', methods=['GET'])
def download_report(report_id: str):
    """
    Download report as Markdown file.
    Download a report in Markdown format.
    
    Download a report in Markdown format.

    Returns the Markdown file.
    """
    try:
        report = ReportManager.get_report(report_id)

        if not report:
            return jsonify({
                "success": False,
                "error": f"Report not found: {report_id}"
            }), 404

        md_path = ReportManager._get_report_markdown_path(report_id)

        if not os.path.exists(md_path):
            # If the Markdown file is missing, generate a temporary one.
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(report.markdown_content)
                temp_path = f.name

            return send_file(
                temp_path,
                as_attachment=True,
                download_name=f"{report_id}.md"
            )

        return send_file(
            md_path,
            as_attachment=True,
            download_name=f"{report_id}.md"
        )

    except Exception as e:
        logger.error(f"Failed to download report: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>', methods=['DELETE'])
def delete_report(report_id: str):
    """Delete report."""
    """Delete a report."""
    try:
        success = ReportManager.delete_report(report_id)

        if not success:
            return jsonify({
                "success": False,
                "error": f"Report not found: {report_id}"
        
        locale = get_request_locale()
        if not success:
            return jsonify({
                "success": False,
                "error": get_error_message('report_not_found', locale).format(report_id=report_id)
            }), 404

        return jsonify({
            "success": True,
            "message": f"Report deleted: {report_id}"
            "message": get_error_message('report_deleted', locale).format(report_id=report_id)
        })

    except Exception as e:
        logger.error(f"Failed to delete report: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Report Agent chat ==============
# ============== Report agent chat endpoint ==============

@report_bp.route('/chat', methods=['POST'])
def chat_with_report_agent():
    """
    Chat with Report Agent (can call retrieval tools).

    Request (JSON): simulation_id (required), message (required), chat_history (optional).

    Returns: response, tool_calls, sources.
    Chat with the report agent.
    
    The report agent can call retrieval tools during the conversation.
    
    Chat with the report agent.

    The report agent can call retrieval tools during the conversation.

    Request (JSON):
        {
            "simulation_id": "sim_xxxx",        // required
            "message": "Explain the trend",     // required
            "chat_history": [                   // optional
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }
    

    Returns:
        {
            "success": true,
            "data": {
                "response": "Agent reply...",
                "tool_calls": [list of called tools],
                "sources": [information sources]
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        message = data.get('message')
        chat_history = data.get('chat_history', [])

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "simulation_id is required"
                "error": "Please provide simulation_id"
        
        report_lang = get_request_locale()
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": get_error_message('missing_simulation_id', report_lang)
            }), 400

        if not message:
            return jsonify({
                "success": False,
                "error": "message is required"
                "error": get_error_message('missing_message', report_lang)
            }), 400
        
                "error": "Please provide message"
            }), 400
        
                "error": "Please provide message"
            }), 400

        # Load simulation and project state.
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"Simulation not found: {simulation_id}"
                "error": f"{get_error_message('simulation_not_found', report_lang)}: {simulation_id}"
            }), 404

        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Project not found: {state.project_id}"
                "error": f"{get_error_message('project_not_found', report_lang)}: {state.project_id}"
            }), 404

        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "Graph ID is missing"
                "error": "Missing graph_id"
                "error": get_error_message('missing_graph_id', report_lang)
            }), 400

        simulation_requirement = project.simulation_requirement or ""
        report_language = report_lang
        

        # Create the agent and run the conversation.
        # 创建Agent并进行对话（使用用户选择的语言）
        agent = ReportAgent(
            graph_id=graph_id,
            simulation_id=simulation_id,
            simulation_requirement=simulation_requirement,
            report_language=report_language
        )

        result = agent.chat(message=message, chat_history=chat_history)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Report progress and sections ==============
# ============== Report progress and sectioned content APIs ==============

@report_bp.route('/<report_id>/progress', methods=['GET'])
def get_report_progress(report_id: str):
    """
    Get report generation progress (live).

    Returns: status, progress, message, current_section, completed_sections, updated_at.
    Get the real‑time generation progress of a report.
    Get the real-time generation progress of a report.

    Returns:
        {
            "success": true,
            "data": {
                "status": "generating",
                "progress": 45,
                "message": "Generating section: Key Findings",
                "current_section": "Key Findings",
                "completed_sections": ["Executive Summary", "Simulation Background"],
                "updated_at": "2025-12-09T..."
            }
        }
    """
    try:
        progress = ReportManager.get_progress(report_id)

        if not progress:
            locale = get_request_locale()
            return jsonify({
                "success": False,
                "error": f"Report not found or progress unavailable: {report_id}"
                "error": get_error_message('report_progress_not_found', locale).format(report_id=report_id)
            }), 404

        return jsonify({
            "success": True,
            "data": progress
        })

    except Exception as e:
        logger.error(f"Failed to get report progress: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/sections', methods=['GET'])
def get_report_sections(report_id: str):
    """
    Get list of generated sections (for streaming).

    Returns: report_id, sections, total_sections, is_complete.
    Get the list of generated sections (sectioned output).

    The frontend can poll this endpoint to incrementally load section
    content without waiting for the entire report to finish.

    Returns:
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "sections": [
                    {
                        "filename": "section_01.md",
                        "section_index": 1,
                        "content": "## Executive Summary\\n\\n..."
                    },
                    ...
                ],
                "total_sections": 3,
                "is_complete": false
            }
        }
    """
    try:
        sections = ReportManager.get_generated_sections(report_id)
        

        # Fetch report status to determine completion
        report = ReportManager.get_report(report_id)
        is_complete = report is not None and report.status == ReportStatus.COMPLETED

        return jsonify({
            "success": True,
            "data": {
                "report_id": report_id,
                "sections": sections,
                "total_sections": len(sections),
                "is_complete": is_complete
            }
        })

    except Exception as e:
        logger.error(f"Failed to get section list: {str(e)}")
        logger.error(f"Failed to get sections: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/section/<int:section_index>', methods=['GET'])
def get_single_section(report_id: str, section_index: int):
    """
    Get single section content.

    Returns: filename, content.
    Get the content of a single section.

    Returns:
        {
            "success": true,
            "data": {
                "filename": "section_01.md",
                "content": "## Executive Summary\\n\\n..."
            }
        }
    """
    try:
        section_path = ReportManager._get_section_path(report_id, section_index)

        if not os.path.exists(section_path):
            locale = get_request_locale()
            return jsonify({
                "success": False,
                "error": f"Section not found: section_{section_index:02d}.md"
                "error": f"Section does not exist: section_{section_index:02d}.md"
                "error": get_error_message('report_section_not_found', locale).format(index=section_index)
            }), 404

        with open(section_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return jsonify({
            "success": True,
            "data": {
                "filename": f"section_{section_index:02d}.md",
                "section_index": section_index,
                "content": content
            }
        })

    except Exception as e:
        logger.error(f"Failed to get section content: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Report status check ==============
# ============== Report status check APIs ==============

@report_bp.route('/check/<simulation_id>', methods=['GET'])
def check_report_status(simulation_id: str):
    """
    Check if simulation has a report and its status (e.g. for unlocking Interview).
    Check whether a simulation has an associated report and its status.

    Used by the frontend to decide whether to unlock the Interview feature.

    Returns:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "has_report": true,
                "report_status": "completed",
                "report_id": "report_xxxx",
                "interview_unlocked": true
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)

        has_report = report is not None
        report_status = report.status.value if report else None
        report_id = report.report_id if report else None
        

        # Only unlock interview when the report has completed
        interview_unlocked = has_report and report.status == ReportStatus.COMPLETED

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "has_report": has_report,
                "report_status": report_status,
                "report_id": report_id,
                "interview_unlocked": interview_unlocked
            }
        })

    except Exception as e:
        logger.error(f"Failed to check report status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Agent log ==============
# ============== Agent log APIs ==============

@report_bp.route('/<report_id>/agent-log', methods=['GET'])
def get_agent_log(report_id: str):
    """
    Get Report Agent execution log (each step: start, sections, tool calls, completion).

    Query: from_line (optional, for incremental fetch).

    Returns: logs, total_lines, from_line, has_more.
    Get the detailed execution log for the Report Agent.

    Provides a real‑time, structured view of every step in the report
    Get the detailed execution log for the Report Agent.

    Provides a real-time, structured view of every step in the report
    generation process, including:
    - Report start, planning start/completion
    - Each section's start, tool calls, LLM responses, completion
    - Report completion or failure

    Query params:
        from_line: Optional starting line (default 0) for incremental fetching.

    Returns:
        {
            "success": true,
            "data": {
                "logs": [
                    {
                        "timestamp": "2025-12-13T...",
                        "elapsed_seconds": 12.5,
                        "report_id": "report_xxxx",
                        "action": "tool_call",
                        "stage": "generating",
                        "section_title": "Executive Summary",
                        "section_index": 1,
                        "details": {
                            "tool_name": "insight_forge",
                            "parameters": {...},
                            ...
                        }
                    },
                    ...
                ],
                "total_lines": 25,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)

        log_data = ReportManager.get_agent_log(report_id, from_line=from_line)

        return jsonify({
            "success": True,
            "data": log_data
        })

    except Exception as e:
        logger.error(f"Failed to get agent log: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/agent-log/stream', methods=['GET'])
def stream_agent_log(report_id: str):
    """
    Get full agent log (all at once).
    Get the full Agent log (all lines at once).

    Returns:
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 25
            }
        }
    """
    try:
        logs = ReportManager.get_agent_log_stream(report_id)

        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })

    except Exception as e:
        logger.error(f"Failed to get agent log: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Console log ==============
# ============== Console log APIs ==============

@report_bp.route('/<report_id>/console-log', methods=['GET'])
def get_console_log(report_id: str):
    """
    Get Report Agent console output (plain text, not structured JSON).

    Query: from_line (optional).

    Returns: logs, total_lines, from_line, has_more.
    Get the Report Agent console output log.

    Streams console‑style text logs (INFO, WARNING, etc.) produced during
    Get the Report Agent console output log.

    Streams console-style text logs (INFO, WARNING, etc.) produced during
    report generation. Unlike the structured JSON agent log, this is raw text.

    Query params:
        from_line: Optional starting line (default 0) for incremental fetching.

    Returns:
        {
            "success": true,
            "data": {
                "logs": [
                    "[19:46:14] INFO: Search completed: 15 relevant facts found",
                    "[19:46:14] INFO: Graph search: graph_id=xxx, query=...",
                    ...
                ],
                "total_lines": 100,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)

        log_data = ReportManager.get_console_log(report_id, from_line=from_line)

        return jsonify({
            "success": True,
            "data": log_data
        })

    except Exception as e:
        logger.error(f"Failed to get console log: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/console-log/stream', methods=['GET'])
def stream_console_log(report_id: str):
    """
    Get full console log (all at once).
    Get the full console log (all lines at once).

    Returns:
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 100
            }
        }
    """
    try:
        logs = ReportManager.get_console_log_stream(report_id)

        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })

    except Exception as e:
        logger.error(f"Failed to get console log: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Tool endpoints (debug) ==============
# ============== Tool invocation APIs (for debugging) ==============

@report_bp.route('/tools/search', methods=['POST'])
def search_graph_tool():
    """
    Graph search tool (debug). Request: graph_id, query, limit (optional).
    Graph search tool endpoint (for debugging).

    Request body (JSON):
        {
            "graph_id": "mirofish_xxxx",
            "query": "search query string",
            "limit": 10
        }
    """
    try:
        data = request.get_json() or {}

        graph_id = data.get('graph_id')
        query = data.get('query')
        limit = data.get('limit', 10)

        if not graph_id or not query:
            locale = get_request_locale()
            return jsonify({
                "success": False,
                "error": "graph_id and query are required"
                "error": "Please provide both graph_id and query"
                "error": get_error_message('report_missing_graph_and_query', locale)
            }), 400

        from ..services.zep_tools import ZepToolsService

        tools = ZepToolsService()
        result = tools.search_graph(
        
        from ..services.memory_factory import get_memory_provider

        provider = get_memory_provider()
        result = provider.search_graph(
            graph_id=graph_id,
            query=query,
            limit=limit
        )

        return jsonify({
            "success": True,
            "data": result.to_dict()
        })

    except Exception as e:
        logger.error(f"Graph search failed: {str(e)}")
        logger.error(f"Failed to search graph: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/tools/statistics', methods=['POST'])
def get_graph_statistics_tool():
    """
    Graph statistics tool (debug). Request: graph_id.
    Graph statistics tool endpoint (for debugging).

    Request body (JSON):
        {
            "graph_id": "mirofish_xxxx"
        }
    """
    try:
        data = request.get_json() or {}

        graph_id = data.get('graph_id')

        if not graph_id:
            locale = get_request_locale()
            return jsonify({
                "success": False,
                "error": "graph_id is required"
                "error": "Please provide graph_id"
                "error": get_error_message('report_missing_graph_id', locale)
            }), 400

        from ..services.zep_tools import ZepToolsService

        tools = ZepToolsService()
        result = tools.get_graph_statistics(graph_id)

        
        from ..services.memory_factory import get_memory_provider

        provider = get_memory_provider()
        result = provider.get_graph_statistics(graph_id)
        
        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Failed to get graph statistics: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
