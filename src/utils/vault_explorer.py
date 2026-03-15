from pathlib import Path
import os
from src.utils.logger import get_app_logger
from src.config.config import OBSIDIAN_VAULT_PATH
from typing import List

log = get_app_logger(name="Vault Explorer")


def scan_vault_content() -> list[Path]:
    """
    Recorre el vault y extrae el contenido de todas las notas
    para que el LLM tenga el contexto completo
    """
    vault_map: list[Path] = []
    # Extensiones que queremmos leer
    allowed_extensions: set[str] = {".md"}

    # Extension que queremos ignorar
    ignored_extensions: set[str] = {".obsidian", ".trash", ".templates"}

    # Recorremos el vault
    # os.walk (root, dirs, files) -> root es la carpeta actual, dirs son las subcarpetas, files son los archivos
    # Es un funcion recursiva que entra en la carpeta y en todas sus subcarpetas
    # dirs es una lista de strings con los nombres de las subcarpetas
    # files es una lista de strings con los nombres de los archivos
    # root es un string con la ruta de la carpeta actual

    # Pendiente actualizar para solo leer directorios especificos? !!!!
    ignored_directories: set[str] = {
        "Index",
        "Excalidraw",
        "Templates",
        "resources",
        "Trash",
        ".venv",
        "attachments",
        "AI Engineer",
    }
    for root, dirs, files in os.walk(Path(OBSIDIAN_VAULT_PATH).parent):
        # Filtramos las carpetas que no queremos leer
        # con dos puntos [:], estás modificando la lista original que os.walk está usando en ese mismo instante.
        dirs[:] = [
            dir
            for dir in dirs
            if dir not in ignored_extensions and dir not in ignored_directories
        ]

        for file in files:
            if Path(file).suffix in allowed_extensions:
                full_path: Path = Path(root) / file
                try:
                    with open(full_path, "r", encoding="utf=8") as file:
                        content: str = file.read()
                        vault_map.append(
                            {
                                "name": full_path.name,
                                "path_file": str(full_path).split("/angel")[-1],
                                "path_folder": str(full_path.parent).split("/angel")[
                                    -1
                                ],
                                "content": content,
                            }
                        )
                except Exception as e:
                    log.error(f"Error al leer el archivo {full_path}: {e}")

    return vault_map


def filter_vault_content(
    vault_content: List[dict], keywords: List[str], top_n: int = 10
) -> List[dict]:
    """
    Filtra el contenido del vault basándose en las palabras clave.
    Ordena por cantidad de coincidencias y devuelve las top_n notas.
    """
    scored_content: List[tuple[int, dict]] = []
    for note in vault_content:
        # Evita reinterados llamados a lower() en cada iteracion
        content_lower = note["content"].lower()
        # contar cuantas keyworkds aparecen en la nota
        match_count = sum(
            1  # count
            for keyword in keywords
            if keyword.lower() in content_lower
        )

        if match_count > 0:
            scored_content.append((match_count, note))

    # Ordenar de mayor a menor por cantidad de matches
    scored_content.sort(key=lambda x: x[0], reverse=True)

    # Devolver solo las notas (sin score), limitadas top_n notas
    return [
        note  # notas
        for _, note in scored_content[:top_n]
    ]


def scan_hubs() -> dict:
    """
    Escanea /hubs y retorna un mapeo de keyword -> hub file path
     Ejemplo: {"Python": "/Users/.../hubs/✱ Python Hub.md", "English": "/Users/.../hubs/✱ English Hub.md"}
    """
    hubs_dir = Path(OBSIDIAN_VAULT_PATH).parent / "hubs"

    hub_map = {}

    # Valido si existe la rutia
    if not hubs_dir.exists():
        log.error("Carpeta hubs / no encontrada")
        return hub_map

    # recorro los arreglos
    for file in hubs_dir.iterdir():
        # si el archivo termina en .md and hub
        if file.suffix == ".md" and "Hub" in file.name:
            # "✱ Python Hub.md" → "Python"
            hub_keyword = file.stem.replace("✱ ", "").replace(" Hub", "")
            hub_map[hub_keyword.lower()] = str(file)

    return hub_map


def format_document(content: str, llm) -> str:

    content_prompt = content

    prompt = f"""
    Formatea el siguiente contenido en formato markdown, crea encabezados, titulos, y demas para mejorar la visutalizacion, agrega emojis que aplique, elimina contenido repetido, pero manten todo el contenido.

    {content_prompt}

    responde con el contenido formateado directamente.
    """

    try:
        response = llm.invoke(prompt)
        return response.content

    except Exception as e:
        log.error(f"Error a formatear document {e}")
        return content
