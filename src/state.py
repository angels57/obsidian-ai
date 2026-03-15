from typing import TypedDict
from pathlib import Path
from pydantic import BaseModel
from typing import Literal, List


class NoteState(TypedDict):
    """Estado de una nota

    Contiene el estado de una nota a lo largo del flujo de análisis.


    """

    # --- Input ---
    source_path: Path  # Ruta original: "Index/5 Underutilized..."
    raw_content: str  # Texto original de la nota

    # --- Analysis (LLM) ---
    clean_title: str  # Título profesional sin basura
    summary: str  # Resumen corto de qué trata la nota
    suggested_filename: str  # Nombre de archivo ideal para Obsidian

    # --- Discovery & Validation ---
    related_notes: List[
        dict
    ]  # Lista de notas similares encontradas: [{"path": "...", "similarity": 0.8}]
    action_type: Literal["CREATE", "MERGE", "LINK"]  # "CREATE", "MERGE" o "LINK"
    merge_target_path: Path  # "[[✱ Python Hub]] | [[✱ Home]]"

    # --- Routing & Structure ---
    target_folder: str  # Carpeta destino: "collections/Professional/Python"
    breadcrumbs: str  # "[[✱ Python Hub]] | [[✱ Home]]"
    final_tags: List[str]  # Lista de etiquetas filtrada y limpia

    # --- Outcome ---
    final_content: str  # El Markdown final listo para escribir
    compliance_status: bool  # ¿Cumple con el manual de Forever Notes?
    logs: List[str]  # Historial de lo que cada nodo ha hecho

    keywords: List[str]  # Lista de palabras clave extraídas de la nota

    hub_path: str


class Node1Response(BaseModel):
    summary: str
    keywords: List[str]


class Node3Response(BaseModel):
    action_type: Literal["CREATE", "MERGE", "LINK"]
    merge_target_path: str
    logs: str


class Node4Response(BaseModel):
    target_folder: str
    logs: str
