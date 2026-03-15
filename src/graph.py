from src.state import NoteState
from langgraph.graph import StateGraph, END
from src.utils.vault_explorer import (
    scan_vault_content,
    filter_vault_content,
    scan_hubs,
    format_document,
)
from src.utils.logger import get_app_logger
from langchain_openai import ChatOpenAI
from src.state import Node3Response, Node4Response, Node1Response
import shutil
from pathlib import Path
import os
from src.config.config import MODEL_NAME, OBSIDIAN_VAULT_PATH, TEMPERATURE

llm = ChatOpenAI(model=str(MODEL_NAME), temperature=float(TEMPERATURE))

log = get_app_logger(name="Vault Explorer")


def node_1_summary_and_keywords(state: NoteState) -> NoteState:
    """1. Node_Summary_and_Keywords (LLM)
    * Misión: Generar un resumen y extraer keywords.
    * Entrada: 5 Underutilized Python Libraries... 1.md.
    * Acción: Genera un resumen y extrae keywords.
    """
    log.info("Nodo 1: Generando resumen y keywords")
    content = state["raw_content"]

    llm_structure = llm.with_structured_output(Node1Response)

    prompt = f"""
    TASKS:
    1. Summarize the following content.
    2. Extract keywords from the following content.

    CONTENT:
    {content}

    '''
    {{
        "summary": "summary",
        "keywords": ["keyword1", "keyword2", "keyword3"],
    }}
    '''
    """
    try:
        response = llm_structure.invoke(prompt)
        state["summary"] = response.summary
        state["keywords"] = response.keywords or []
        state["logs"].append("Node 1: Generando resumen y keywords")
    except Exception as e:
        log.error(f"Nodo 1:Error al generar resumen y keywords: {e}")
        state["keywords"] = []
        state["summary"] = ""

    return state


def node_2_semantic_scanner(state: NoteState) -> NoteState:
    """2. Node_Semantic_Scanner (Keyword Matching)
    * Misión: Buscar colisiones de conocimiento por keywords.
    * Acción: Filtra notas del vault que compartan keywords con la nota nueva.
    * Salida: Lista de notas relacionadas con resumen compacto."""

    log.info("Nodo 2: Escaneando el vault")
    vault_content = scan_vault_content()

    keywords = state["keywords"]
    if keywords == []:
        log.info("Nodo 2: No keywords found, skipping scan")
        state["related_notes"] = []
        state["logs"].append("Node 2: No keywords found")
        return state
    note_related = []
    filtered_vault_content = filter_vault_content(vault_content, keywords)
    # Valida si la lista no esta vacia
    if filtered_vault_content:
        for note in filtered_vault_content:
            # Extraer las primeras lineas no vacias como resumen
            lines = note["content"].split("\n")
            summary_lines = [line for line in lines if line.strip()][:3]
            summary = "\n".join(summary_lines)
            note_related.append(
                {
                    "title": note["name"],
                    "path": note["path_file"],
                    "content": summary,
                }
            )
        state["related_notes"] = note_related
        state["logs"].append(
            f"Node 2: Added {len(filtered_vault_content)} related notes"
        )
    else:
        state["related_notes"] = []
        state["logs"].append("Node 2: No related notes found")
    return state


def node_3_knowledge_integrator(state: NoteState) -> NoteState:
    """3. Node_Knowledge_Integrator (LLM - Punto de Decisión)
    Este nodo se preocupa por la No Redundancia (evitar el "cementerio digital").
    * Pregunta clave: "¿Esta información ya la tengo en otro sitio o es conocimiento nuevo?"
    * Misión: Comparar la nota actual con las notas similares encontradas en el Nodo 2.
    * Decisión (Action Type):
        * MERGE (Fusión): "Ya tienes una nota de Python Automation. No crees otra; añade estas 5 librerías a la nota existente".
        * LINK (Enlace): "Es un tema nuevo, pero se relaciona con CLI Development. Crea una nota nueva pero añade un enlace See also".
        * CREATE (Creación): "Es conocimiento totalmente nuevo. Procede a crear un archivo independiente".
    """

    log.info("Node 3: Integrating knowledge")
    note_content = state["summary"]
    related_notes = state["related_notes"]

    if not related_notes:
        log.info("Node 3: No related notes found")
        state["action_type"] = "CREATE"
        state["merge_target_path"] = ""
        state["logs"].append("Node 3: No related notes found, defaulting to CREATE")
        return state

    llm_structure = llm.with_structured_output(Node3Response)

    prompt = f"""
    TASKS:
    1.   Misión: Comparar la nota actual con las notas similares encontradas.
    2.  Decisión (Action Type):
        * MERGE (Fusión): Ejemplo: La nota nueva cubre el MISMO tema principal que una existente. 
  Podrían fusionarse sin perder coherencia.
        * CREATE (Creación): La nota nueva no tiene overlap significativo con ninguna existente.

    NOTA NUEVA:
    {note_content}
    NOTAS EXISTENTES:
    {related_notes}

     INSTRUCCIONES:
    - Si decides MERGE, en merge_target_path coloca la ruta de la nota existente (usa el path de las notas relacionadas).
    - Si decides LINK o CREATE, deja merge_target_path vacío "".

    '''
    {{
        "action_type": "MERGE o CREATE",
        "merge_target_path": "",
        "logs": "Explica la razon de la decision",
    }}
    '''
    
    """

    try:
        response = llm_structure.invoke(prompt)
        state["action_type"] = response.action_type
        state["merge_target_path"] = response.merge_target_path or ""
        state["logs"].append(f" Added {response.action_type}: {response.logs}")
    except Exception as e:
        log.error(f"Error al integrar conocimiento: {e}")
        state["logs"].append(f"Error: {e}")
        state["action_type"] = "CREATE"
        state["merge_target_path"] = ""

    return state


def route_after_knowledge_integrator(state: NoteState) -> str:
    """
    Decide el siguiente nodo en action_type.
    """
    log.info(f"Routing the folder: {state['action_type']}")
    if state["action_type"] == "MERGE":
        return "file_system_executor"  # Salida folder routes
    else:  # CREATE O LINK
        return "folder_router"


def node_4_folder_router(state: NoteState) -> NoteState:
    """4. Node_Folder_Router (LLM)
    Este nodo se preocupa por la Arquitectura (cumplir el manual "Forever Notes").
    * Pregunta clave: "¿A qué área de mi vida o carrera pertenece este conocimiento?"
    * Misión: Analizar el contexto del contenido frente a las reglas del Paso 4 del manual.
    * Decisión (Target Folder):
        * Professional: "Estas librerías son herramientas de ingeniería. Van a collections/Professional/Python/".
        * Personal: "Es un resumen de un video para entretenimiento. Va a collections/Personal/Hobbies/".
        * Projects: "Estas librerías las necesitas para el proyecto PDF AI. Van a collections/Projects/PDF AI/".
    """
    log.info("Node 4: Enrutando la carpeta")
    content = state["summary"]
    related_content = state["related_notes"]
    llm_structure = llm.with_structured_output(Node4Response)

    prompt = f""" 
        TASK:
    Analiza el contenido de la nota y decide en qué carpeta del vault debe almacenarse.
    NOTA:
    {content}
    NOTAS RELACIONADAS:
    {related_content}
    CARPETAS DISPONIBLES:
        - collections/Professional/  (temas de ingeniería, trabajo, herramientas técnicas)
        - collections/Personal/  (hobbies, entretenimiento, vida personal)
        - collections/Projects/  (proyectos activos específicos)
    INSTRUCCIONES:
    - Elige una de las carpetas disponibles como base.
    - Puedes agregar subcarpetas si es necesario (ej: collections/Professional/Python/).
    - Responde solo con la ruta de la carpeta.
    '''
    {{
        "target_folder": "collections/Professional/Python/",
        "logs": "Razón de la decisión"
    }}
    '''

    """

    try:
        response = llm_structure.invoke(prompt)
        state["target_folder"] = response.target_folder
        state["logs"].append(f"ADD folder path {response.logs}")

    except Exception as e:
        log.error(f"Error durante la ejecucion {e}")
        state["target_folder"] = ""
        state["logs"].append(f"Error: {e}")

    return state


def node_5_file_system_executor(state: NoteState) -> NoteState:
    """5. Node_File_System_Executor (System Tool)
     Este nodo es el brazo ejecutor (Puro código/shell).
    * Pregunta clave: "¿Dónde y cómo escribo el archivo físico?"
    * Misión: Ejecutar los comandos de sistema para mover el archivo, escribir el contenido final y borrar el rastro en la carpeta temporal.
    * Resultado: Archivo escrito en su destino final.
    """
    log.info(f"Node 5: Ejecutando el sistema de archivos {state['action_type']}")
    source_path = state["source_path"]
    action = state["action_type"]

    if action == "CREATE" or action == "LINK":
        try:
            target = state["target_folder"]
            if str(target).startswith("/"):
                target = f"{Path(OBSIDIAN_VAULT_PATH).parent}{target}"
            else:
                target = f"{Path(OBSIDIAN_VAULT_PATH).parent}/{target}"
            os.makedirs(target, exist_ok=True)
            shutil.move(str(source_path), target)
            state["logs"].append(f"File moved to: {target}")
            log.info(f"The file create in {target}")
        except Exception as e:
            log.error(f"Error al mover la nota: {e}")
            state["logs"].append(f"Error: {e}")

    elif action == "MERGE":
        # leer la nota existente
        try:
            merge_target = state["merge_target_path"]

            if str(merge_target).startswith("/"):
                merge_target = f"{Path(OBSIDIAN_VAULT_PATH).parent}{merge_target}"
            else:
                merge_target = f"{Path(OBSIDIAN_VAULT_PATH).parent}/{merge_target}"

            with open(merge_target, "r", encoding="utf-8") as f:
                existing_content = f.read()

            # leer la nota nueva y combinar
            with open(str(source_path), "r", encoding="utf-8") as f:
                new_content = f.read()

            merged_content = f"{existing_content}\n\n---\n\n{new_content}"

            # reescribir la nota existente
            with open(merge_target, "w", encoding="utf-8") as f:
                f.write(merged_content)

            # borrar la nota nueva
            os.remove(str(source_path))

            state["logs"].append(f"File merged to: {merge_target}")
            log.info(f"The file MERGE with {merge_target}")
        except Exception as e:
            log.error(f"Error al fusionar la nota: {e}")
            state["logs"].append(f"Error: {e}")

    return state


def node_6_metada_architect(state: NoteState) -> NoteState:
    """6. Node_Metadata_Architect (Rule-based)
    * Misión: Agregar breadcrumbs y tags según el manual Forever Notes.
    """
    log.info("Node 6: Agregando metadata")

    # En merge, la nota existente ya tiene metadata
    if state["action_type"] == "MERGE":
        log.info("Node 6: MERGE - skipping (la nota ya tiene metada)")
        state["logs"].append("Node 6: Skipped (MERGE)")
        return state

    # 1. Determinar ruta de la nota final
    target = state["target_folder"]
    if str(target).startswith("/"):
        note_dir = f"{Path(OBSIDIAN_VAULT_PATH).parent}{target}"
    else:
        note_dir = f"{Path(OBSIDIAN_VAULT_PATH).parent}/{target}"
    note_path = os.path.join(note_dir, Path(state["source_path"]).name)

    # 2. Buscar el hub correspondiente dinámicamente
    # target_folder = "collections/Professional/Python/" → subcarpeta = "Python"
    parts = [part for part in target.split("/") if part and part != "collections"]
    hub_map = scan_hubs()

    # Buscar match: primero por la subcarpeta mas especifica (ej:python)
    hub_path = None
    hub_name = None

    for part in reversed(
        parts
    ):  # ["Python", "Professional"] — empieza por el más específico
        if part.lower() in hub_map:
            hub_path = hub_map[part.lower()]  # "/Users/.../hubs/✱ Python Hub.md"
            hub_name = f"✱ {part} Hub"  # "✱ Python Hub"
            break  # Encontro match, no sigue buscando.
    state["hub_path"] = hub_path
    # Generar nav
    if hub_name:
        breadcrumbs = f"[[{hub_name}]] | [[✱ Home]]"
        # Resultado: "[[Python Hub]] | [[✱ Home]]"
    else:
        breadcrumbs = "[[✱ Home]]"
        # Si no encontro hub, solo enlaza a home

    # Generar tags
    note_title = Path(state["source_path"]).stem.lower()
    # "FastApi.md" → .stem quita extensión → "FastApi" → .lower() → "fastapi"
    tags = []
    for keyword in state["keywords"]:  # ["FastAPI", "REST", "CRUD"]
        tag = keyword.replace(" ", "_").lower()  # "REST" -> rest
        if tag != note_title:  # Regla del manual: tag != titulo
            tags.append(f"#{tag}")  # ["#fastapi", "#rest", "#crud"]

    tags_str = " ".join(tags)  # "#fastapi #rest #crud"

    # Escribir en el archivo
    try:
        with open(note_path, "r", encoding="utf-8") as file:
            note_content = file.read()

        # Estructura: # Título \n breadcrumbs \n\n contenido \n\n ## Tags. \n tags
        lines = format_document(content=note_content, llm=llm)
        lines = lines.replace("```markdown", "").replace("```", "").split("\n")
        title_line = lines[0] if lines else ""

        new_content = f"{title_line}{breadcrumbs}\n"
        new_content += "\n".join(lines[1:])  # resto del contenido
        new_content += f"\n\n## Tags.\n{tags_str}\n"

        with open(note_path, "w", encoding="utf-8") as file:
            file.write(new_content)

        state["breadcrumbs"] = breadcrumbs
        state["final_tags"] = state["keywords"]
        state["logs"].append(f"Node 6: Metadata added | Hub: {hub_name}")
        log.info(f"Node 6: Added breadcrumbs [{breadcrumbs}] and tags to {note_path}")

    except Exception as e:
        log.error(f"Error escribiendo en el archibo {e}")

    return state


def node_7_hub_indexer(state: NoteState) -> NoteState:
    """7. Node_Hub_Indexer (Rule-based)
    * Misión: Agregar un link a la nota nueva en el Hub correspondiente.
    """
    log.info("Node 7: Indexando en hub")
    # En MERGE, la nota ya está indexada en el hub
    if state["action_type"] == "MERGE":
        log.info("Node 7: MERGE - skipping (nota ya indexada)")
        state["logs"].append("Node 7: Skipped (MERGE)")
        return state

    hub_path = state["hub_path"]

    # Si no hay hub, no hay nada que indexar
    if not hub_path:
        log.info("Node 7: No hub found, skipping")
        state["logs"].append("Node 7: No hub found")
        return state

    try:
        # Nombre de la nota (sin extension)
        note_name = Path(state["source_path"]).stem
        new_link = f"- [[{note_name}]]"

        # Leer el hub
        with open(hub_path, "r", encoding="utf-8") as file:
            hub_content = file.read()

        # Verficar que el link no exista ya
        if new_link in hub_content:
            log.info(f"Node 7: {note_name} ya esta en el hub")
            state["logs"].append(f"Node 7: {note_name} already indexed")
            return state

        # Insertar antes de '## Tags", (Ultimas seccion del hub)
        if "## Topics" in hub_content:
            hub_content = hub_content.replace("## Topics", f"## Topics\n{new_link}")
        else:
            # Si no tiene seccion Tags, agregar al final
            hub_content += f"\n{new_link}\n"

        with open(hub_path, "w", encoding="utf-8") as file:
            file.write(hub_content)

        state["logs"].append(f"Node 7: Added [[{note_name}]] to hub")
        log.info(f"Node 7: Indexed [[{note_name}]] in {hub_path}")

    except Exception as e:
        log.error(f"Node 7: Error: {e}")
        state["logs"].append(f"Error: {e}")

    return state


# 1. Creamos el grafo
workflow = StateGraph(NoteState)

# 2. Agregamos los nodos
workflow.add_node("input_sanitizer", node_1_summary_and_keywords)
workflow.add_node("semantic_scanner", node_2_semantic_scanner)
workflow.add_node("knowledge_integrator", node_3_knowledge_integrator)
workflow.add_node("folder_router", node_4_folder_router)
workflow.add_node("file_system_executor", node_5_file_system_executor)
workflow.add_node("metada_architect", node_6_metada_architect)
workflow.add_node("hub_indexer", node_7_hub_indexer)

# 3. Definimos el flujo
workflow.set_entry_point("input_sanitizer")
workflow.add_edge("input_sanitizer", "semantic_scanner")
workflow.add_edge("semantic_scanner", "knowledge_integrator")

workflow.add_conditional_edges(
    "knowledge_integrator",  # Nodo origen
    route_after_knowledge_integrator,  # funcion que decide
    {
        "folder_router": "folder_router",  # si retorna folder_router va a folder router
        "file_system_executor": "file_system_executor",  # si retorna file_system_executor va a file_system_executor
    },
)
workflow.add_edge("folder_router", "file_system_executor")
workflow.add_edge("file_system_executor", "metada_architect")
workflow.add_edge("metada_architect", "hub_indexer")
workflow.add_edge("hub_indexer", END)


# 4. Compilamos el grafo
app = workflow.compile()
