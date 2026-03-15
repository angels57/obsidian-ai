from src.utils.logger import get_app_logger
from pathlib import Path
from src.graph import app


log = get_app_logger(name="Run Workflow")


def run_analysis_workflow(file_path: Path):
    """Ejecuta el flujo de análisis en una nota específica."""

    if not file_path.exists():
        log.error(f"El archivo {file_path} no existe")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Preparar el estado inicial
    initial_state = {
        "source_path": file_path,
        "raw_content": content,
        "clean_title": "",
        "summary": "",
        "suggested_filename": "",
        "related_notes": [],
        "action_type": "",
        "cross_link": "",
        "target_folder": "",
        "breadcrumbs": "",
        "final_tags": [],
        "final_content": "",
        "compliance_status": False,
        "logs": [],
        "keywords": [],
        "hub_path": [],
    }

    # 2. Ejecutar el grafo
    log.info(f"Ejecutando flujo Langgraph para {file_path.name}")
    try:
        app.invoke(initial_state)
    except Exception as e:
        log.error(f"Error al ejecutar el flujo: {e}")
        return
