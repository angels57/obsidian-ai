import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configuración de Rutas (Caminos)
# Usamos Pathlib para que funcione igual en Windows, Mac o Linux
OBSIDIAN_VAULT_PATH: Path = Path(
    os.getenv("OBSIDIAN_VAULT_PATH")
)  # evita errores con las barras inclinadas (/ vs \) entre Windows y Mac.
LOG_DIR: Path = Path("logs/app.log")

# Configuración del LLM
MODEL_NAME: str = "gpt-4o-mini"
TEMPERATURE: float = 0.1


# Validacion basica al arrancar el sistema
def validate_config():
    if not OBSIDIAN_VAULT_PATH.exists():
        raise FileNotFoundError(f"No se encontro la carpeta: {OBSIDIAN_VAULT_PATH}")
    if not LOG_DIR.exists():
        os.makedirs(LOG_DIR)
    return True
