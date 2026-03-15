from src.utils.logger import get_app_logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.config.config import OBSIDIAN_VAULT_PATH, validate_config
import sys
import time
from pathlib import Path
from src.run_workflow import run_analysis_workflow

log = get_app_logger(name="Monitor")


class ObsidianHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # This trigger when a file is edited
        if not event.is_directory:
            log.info(f"File Modified: {event.src_path.split('/angel')[-1]}")

    def on_created(self, event):
        # Solo nos interesan los archivos .md
        if not event.is_directory and event.src_path.endswith(".md"):
            file_path: Path = Path(event.src_path)
            log.info(f"New note detected: {file_path.name}")

            # Aqui llamaremos la funcion langgraph
            self.process_note(file_path)

    def process_note(self, file_path: Path):
        """Punto de conexión con el cerebro (LangGraph)."""
        log.info(f"Processing note: {file_path.name} the flow analysis")
        run_analysis_workflow(file_path)


def start_monitor():
    """Inicia el monitor de Obsidian"""
    log.info("Starting the monitor")

    if not validate_config():
        log.error("La configuracion no es valida, por favor revisa el archivo .env")
        sys.exit(1)

    log.info(f"Vault detectado en la carpeta: {OBSIDIAN_VAULT_PATH}")

    path_to_watch: str = OBSIDIAN_VAULT_PATH
    event_handler: ObsidianHandler = ObsidianHandler()
    observer: Observer = Observer()
    # recursive=False porque solo queremos vigilar la raíz del Inbox
    observer.schedule(event_handler=event_handler, path=path_to_watch, recursive=False)

    observer.start()
    try:
        log.info("El sistema esta corriendo, presiona Ctrl+C para detenerlo")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        log.info("Deteniendo el sistema")
    observer.join()
