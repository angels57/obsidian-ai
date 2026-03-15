from src.monitor import start_monitor
from src.utils.logger import get_app_logger
from src.config.config import validate_config
import sys


log = get_app_logger(name="Main")


def start_app():

    # Validar que el Vault y el .env están bien
    if not validate_config():
        sys.exit(1)

    # Arrancamos el monitor (Watchdog)
    # Importante: dentro de monitor.py, la función process_note
    # ahora llamará a run_analysis_workflow

    try:
        start_monitor()
    except Exception as e:
        log.error(f"Error al iniciar el sistema: {e}")


if __name__ == "__main__":
    start_app()
