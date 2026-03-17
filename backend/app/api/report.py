"""
Report API routes.
Provides endpoints for report generation, retrieval, and chat.
"""

import os
import threading
from flask import request, jsonify, send_file, after_this_request

from . import report_bp
from ..utils.request_locale import get_request_locale
from ..utils.error_messages import get_error_message
from ..services.report_agent import ReportAgent, ReportManager, ReportStatus
from ..services.simulation_manager import SimulationManager
from ..models.project import ProjectManager
from ..models.task import TaskManager, TaskStatus
from ..utils.logger import get_logger
from ..utils.validators import validate_safe_id

logger = get_logger('mirofish.api.report')


# ============== Report generation endpoints ==============

@report_bp.route('/generate', methods=['POST'])
def generate_report():
    """Generate a simulation analysis report asynchronously. Returns task_id immediately. JSON: simulation_id, force_regenerate."""
    try:
        data = request.get_json() or {}

        locale = get_request_locale()

        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": get_error_message('report_missing_sim_id', locale)
            }), 400

        force_regenerate = data.get('force_regenerate', False)

        # Load the simulation.
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": get_error_message('report_sim_not_found', locale).format(simulation_id=simulation_id)
            }), 404

        # Reuse an existing completed report unless forced to regenerate.
        if not force_regenerate:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "report_id": existing_report.report_id,
                        "status": "completed",
                        "message": get_error_message('report_already_exists', locale),
                        "already_generated": True
                    }
                })

        # Load the project.
        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": get_error_message('report_project_not_found', locale).format(project_id=state.project_id)
            }), 404

        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": get_error_message('report_missing_graph', locale)
            }), 400

        simulation_requirement = project.simulation_requirement
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": get_error_message('report_missing_requirement', locale)
            }), 400

        # Capture user language before starting thread (no Flask request context in thread).
        report_language = locale

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
                    message=get_error_message('report_init_agent', report_language)
                )

                # Create the report agent.
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
                    task_manager.fail_task(task_id, report.error or get_error_message('report_gen_failed', report_language))

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
    """Query report generation task progress. JSON: task_id (optional), simulation_id (optional)."""
    try:
        locale = get_request_locale()
        data = request.get_json() or {}

        task_id = data.get('task_id')
        simulation_id = data.get('simulation_id')

        # If simulation_id is provided, first check whether the report is already done.
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
                        "message": get_error_message('report_already_generated', locale),
                        "already_completed": True
                    }
                })

        if not task_id:
            return jsonify({
                "success": False,
                "error": get_error_message('report_missing_task_or_sim_id', locale)
            }), 400

        task_manager = TaskManager()
        task = task_manager.get_task(task_id)

        if not task:
            return jsonify({
                "success": False,
                "error": get_error_message('report_task_not_found', locale).format(task_id=task_id)
            }), 404

        return jsonify({
            "success": True,
            "data": task.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to query task status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Report retrieval endpoints ==============

@report_bp.route('/<report_id>', methods=['GET'])
def get_report(report_id: str):
    """Get report details."""
    try:
        validate_safe_id(report_id, "report_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    try:
        report = ReportManager.get_report(report_id)

        if not report:
            locale = get_request_locale()
            return jsonify({
                "success": False,
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
    """Get a report by simulation ID."""
    try:
        validate_safe_id(simulation_id, "simulation_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    try:
        report = ReportManager.get_report_by_simulation(simulation_id)

        if not report:
            locale = get_request_locale()
            return jsonify({
                "success": False,
                "error": get_error_message('report_no_report_for_sim', locale).format(simulation_id=simulation_id),
                "has_report": False
            }), 404

        return jsonify({
            "success": True,
            "data": report.to_dict(),
            "has_report": True
        })

    except Exception as e:
        logger.error(f"Failed to get report by simulation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/list', methods=['GET'])
def list_reports():
    """List all reports. Query: simulation_id (optional), limit (default 50)."""
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
    """Download a report in Markdown format."""
    try:
        validate_safe_id(report_id, "report_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

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

            @after_this_request
            def cleanup(response):
                try:
                    if temp_path and os.path.exists(temp_path):
                        os.unlink(temp_path)
                except OSError:
                    pass
                return response

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
    """Delete a report."""
    try:
        validate_safe_id(report_id, "report_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    try:
        locale = get_request_locale()
        success = ReportManager.delete_report(report_id)

        if not success:
            return jsonify({
                "success": False,
                "error": get_error_message('report_not_found', locale).format(report_id=report_id)
            }), 404

        return jsonify({
            "success": True,
            "message": get_error_message('report_deleted', locale).format(report_id=report_id)
        })

    except Exception as e:
        logger.error(f"Failed to delete report: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Report agent chat endpoint ==============

@report_bp.route('/chat', methods=['POST'])
def chat_with_report_agent():
    """Chat with the report agent. JSON: simulation_id, message, chat_history (optional)."""
    try:
        data = request.get_json() or {}

        report_lang = get_request_locale()
        simulation_id = data.get('simulation_id')
        message = data.get('message')
        chat_history = data.get('chat_history', [])

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": get_error_message('missing_simulation_id', report_lang)
            }), 400

        if not message:
            return jsonify({
                "success": False,
                "error": get_error_message('missing_message', report_lang)
            }), 400

        # Load simulation and project state.
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"{get_error_message('simulation_not_found', report_lang)}: {simulation_id}"
            }), 404

        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"{get_error_message('project_not_found', report_lang)}: {state.project_id}"
            }), 404

        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": get_error_message('missing_graph_id', report_lang)
            }), 400

        simulation_requirement = project.simulation_requirement or ""
        report_language = report_lang

        # Create the agent and run the conversation.
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


# ============== Report progress and sectioned content APIs ==============

@report_bp.route('/<report_id>/progress', methods=['GET'])
def get_report_progress(report_id: str):
    """Get the real-time generation progress of a report."""
    try:
        validate_safe_id(report_id, "report_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    try:
        progress = ReportManager.get_progress(report_id)

        if not progress:
            locale = get_request_locale()
            return jsonify({
                "success": False,
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
    """Get the list of generated sections (for incremental loading)."""
    try:
        validate_safe_id(report_id, "report_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    try:
        sections = ReportManager.get_generated_sections(report_id)

        # Fetch report status to determine completion.
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
        logger.error(f"Failed to get sections: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/section/<int:section_index>', methods=['GET'])
def get_single_section(report_id: str, section_index: int):
    """Get the content of a single section."""
    try:
        validate_safe_id(report_id, "report_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    try:
        section_path = ReportManager._get_section_path(report_id, section_index)

        if not os.path.exists(section_path):
            locale = get_request_locale()
            return jsonify({
                "success": False,
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


# ============== Report status check APIs ==============

@report_bp.route('/check/<simulation_id>', methods=['GET'])
def check_report_status(simulation_id: str):
    """Check if simulation has a report and its status (used to unlock Interview feature)."""
    try:
        validate_safe_id(simulation_id, "simulation_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    try:
        report = ReportManager.get_report_by_simulation(simulation_id)

        has_report = report is not None
        report_status = report.status.value if report else None
        report_id = report.report_id if report else None

        # Only unlock interview when the report has completed.
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


# ============== Agent log APIs ==============

@report_bp.route('/<report_id>/agent-log', methods=['GET'])
def get_agent_log(report_id: str):
    """Get the Report Agent execution log. Query: from_line (optional, for incremental fetch)."""
    try:
        validate_safe_id(report_id, "report_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

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
    """Get the full Agent log (all lines at once)."""
    try:
        validate_safe_id(report_id, "report_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

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


# ============== Console log APIs ==============

@report_bp.route('/<report_id>/console-log', methods=['GET'])
def get_console_log(report_id: str):
    """Get the Report Agent console output log. Query: from_line (optional)."""
    try:
        validate_safe_id(report_id, "report_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

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
    """Get the full console log (all lines at once)."""
    try:
        validate_safe_id(report_id, "report_id")
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

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
