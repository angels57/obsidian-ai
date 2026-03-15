from pathlib import Path
from src.utils.logger import get_app_logger
import shutil
import os

log = get_app_logger(name="File Ops")

manual_path: Path = Path(os.getenv("SYSTEM_PROMPT_BASE"))


def read_note_file(file_path: Path) -> str:
    """Lee el contenido de un archivo .md"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        log.error(f"Error al leer el archivo: {file_path} - {e}")
        return ""


def move_note_to_processed(source_path: Path, destination_folder: Path) -> bool:
    """Mueve una nota a una nueva carpeta de destino."""
    try:
        # Asegura que la carpeta de destino exista
        destination_folder.mkdir(parents=True, exist_ok=True)
        destination_path = destination_folder / source_path.name

        if destination_path.exists():
            log.warning(
                f"El archivo {source_path.name} ya existe en el destino: {destination_path} sobreescribiend."
            )

        # (Shell Utilities) Mueve el archivo
        shutil.move(str(source_path), str(destination_path))
        log.info(f"✅ movido a: {source_path.name} -> {destination_folder.name}")
        return True

    except Exception as e:
        log.error(f"❌ Error al mover {source_path.name}: {e}")
        return False


def get_note_title(file_path: Path) -> str:
    """Obtiene el titulo de la nota desde el nombre del archivo."""
    return file_path.stem


def read_manual() -> str:
    """Lee el manual de Obsidian. FOREVER NOTES"""
    try:
        with open(manual_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        log.error(f"Error al leer el archivo: {manual_path} - {e}")
        return ""
