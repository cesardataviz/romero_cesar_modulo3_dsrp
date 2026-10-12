# conftest.py
# Configuración compartida de pytest: se ejecuta antes de las pruebas.
import pytest

from cargar_datos import reconstruir_base


@pytest.fixture(scope="session", autouse=True)
def base_de_datos():
    """Reconstruye SQLite desde los CSV una vez, para que todas las pruebas partan de los mismos datos."""
    reconstruir_base()
