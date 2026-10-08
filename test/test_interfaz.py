
# test_interfaz.py

# Importamos pytest para poder realizar las pruebas
import pytest
import sys
import os

# Esto le indica a Python que busque también en la carpeta principal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importamos la clase que queremos probar
from clase_interfaz import Interfaz


# ============================================================
# OBJETOS SIMULADOS (MOCKS)
# ============================================================
# Como estamos haciendo una prueba UNITARIA de Interfaz,
# no queremos depender del funcionamiento real de Monitoreo,
# GestorAlertas, Lector o BaseDeDatos.
#
# Por eso creamos clases pequeñas que simulan su comportamiento.


class GestorAlertasMock:
    """Simula el comportamiento de GestorAlertas."""

    def __init__(self):
        self.umbral_min = None
        self.umbral_max = None
        self.alerta_silenciada = False

    def silenciar_alerta(self):
        """Simula la función de silenciar la alarma."""
        self.alerta_silenciada = True


class MonitoreoMock:
    """Simula el comportamiento de Monitoreo."""

    def __init__(self):
        self.gorra = None
        self.sesion_iniciada = False
        self.sesion_finalizada = False

    def iniciar_sesion(self, num_gorro):
        """Simula el inicio de una sesión."""
        self.gorra = num_gorro
        self.sesion_iniciada = True

    def finalizar_sesion(self):
        """Simula la finalización de una sesión."""
        self.sesion_finalizada = True


class LectorMock:
    """Simula el comportamiento del Lector."""

    def __init__(self, temperatura=None):
        self.temperatura = temperatura

    def leer_temperatura(self):
        """Devuelve una temperatura simulada."""
        return self.temperatura


class BaseDatosMock:
    """Simula el comportamiento de la Base de Datos."""

    def __init__(self):
        self.paciente = None

    def guardar_paciente(self, id_paciente, num_sesion):
        """Simula el guardado de un paciente."""
        self.paciente = (id_paciente, num_sesion)


# ============================================================
# PRUEBA 1 - INICIALIZACIÓN
# ============================================================

def test_inicializacion_interfaz():
    """
    Verifica que cuando se crea un objeto Interfaz,
    sus atributos tengan los valores iniciales correctos.
    """

    interfaz = Interfaz()

    # Estado inicial de la conexión
    assert interfaz.estado_conexion == "DESCONECTADO"

    # Temperatura inicial
    assert interfaz.temp_actual == 0.0

    # Las dependencias inicialmente son None
    assert interfaz.monitoreo is None
    assert interfaz.gestor_alertas is None
    assert interfaz.clase_lector is None


# ============================================================
# PRUEBA 2 - ACTUALIZAR ESTADO DE CONEXIÓN
# ============================================================

def test_actualizar_estado_conexion():
    """
    Verifica que la interfaz cambie correctamente
    entre CONECTADO y DESCONECTADO.
    """

    interfaz = Interfaz()

    # Simulamos que Arduino se conectó
    interfaz.actualizar_estado_conexion(True)

    # El estado debería ser CONECTADO
    assert interfaz.estado_conexion == "CONECTADO"

    # Simulamos que Arduino se desconectó
    interfaz.actualizar_estado_conexion(False)

    # El estado debería ser DESCONECTADO
    assert interfaz.estado_conexion == "DESCONECTADO"


# ============================================================
# PRUEBA 3 - CONFIGURAR UMBRALES
# ============================================================

def test_configurar_umbrales():
    """
    Verifica que configurar_umbrales() guarde correctamente
    la temperatura mínima y máxima en GestorAlertas.
    """

    # Creamos un GestorAlertas simulado
    gestor = GestorAlertasMock()

    # Creamos la interfaz utilizando ese gestor
    interfaz = Interfaz(gestor_alertas=gestor)

    # Configuramos el rango térmico
    interfaz.configurar_umbrales(15, 18)

    # Comprobamos que los valores se hayan guardado
    assert gestor.umbral_min == 15.0
    assert gestor.umbral_max == 18.0


# ============================================================
# PRUEBA 4 - CONFIGURAR UMBRALES INCORRECTAMENTE
# ============================================================

def test_configurar_umbrales_invalidos():
    """
    Verifica que la interfaz genere un ValueError cuando
    la temperatura mínima sea mayor o igual a la máxima.
    """

    gestor = GestorAlertasMock()
    interfaz = Interfaz(gestor_alertas=gestor)

    # pytest.raises verifica que se produzca una excepción.
    with pytest.raises(ValueError):

        # 20 no puede ser la temperatura mínima
        # si 18 es la temperatura máxima.
        interfaz.configurar_umbrales(20, 18)


# ============================================================
# PRUEBA 5 - REGISTRAR PACIENTE
# ============================================================

def test_registrar_paciente():
    """
    Verifica que registrar_paciente() envíe correctamente
    el ID del paciente y el número de sesión a la Base de Datos.
    """

    # Creamos la base de datos simulada
    base_datos = BaseDatosMock()

    # Creamos la interfaz
    interfaz = Interfaz()

    # Agregamos la base de datos a la interfaz.
    # En tu clase actual este atributo no está en __init__,
    # pero registrar_paciente() busca self.base_dato.
    interfaz.base_dato = base_datos

    # Registramos un paciente
    interfaz.registrar_paciente(123, 2)

    # Comprobamos que la base de datos haya recibido
    # correctamente los datos.
    assert base_datos.paciente == (123, 2)


# ============================================================
# PRUEBA 6 - REGISTRAR GORRA
# ============================================================

def test_registrar_gorra():
    """
    Verifica que registrar_gorra() envíe el número de gorra
    al objeto Monitoreo y que se inicie la sesión.
    """

    monitoreo = MonitoreoMock()

    interfaz = Interfaz(monitoreo=monitoreo)

    # Registramos la gorra número 1
    interfaz.registrar_gorra(1)

    # Comprobamos que Monitoreo haya recibido el número
    assert monitoreo.gorra == 1

    # Comprobamos que la sesión se haya iniciado
    assert monitoreo.sesion_iniciada is True


# ============================================================
# PRUEBA 7 - BOTÓN GUARDAR
# ============================================================

def test_al_presionar_guardar():
    """
    Verifica el comportamiento del botón "Guardar".

    Al presionar Guardar debería:
    1. Registrar al paciente.
    2. Registrar la gorra.
    3. Iniciar la sesión.
    4. Activar datos_guardados.
    """

    # Creamos las dependencias simuladas
    base_datos = BaseDatosMock()
    monitoreo = MonitoreoMock()

    # Creamos la interfaz
    interfaz = Interfaz(monitoreo=monitoreo)

    # Agregamos la base de datos
    interfaz.base_dato = base_datos

    # Simulamos que el usuario presiona Guardar
    interfaz.al_presionar_guardar(
        id_paciente=123,
        num_sesion=2,
        num_gorro=1
    )

    # Verificamos que el paciente haya sido registrado
    assert base_datos.paciente == (123, 2)

    # Verificamos que la gorra haya sido registrada
    assert monitoreo.gorra == 1

    # Verificamos que la sesión se haya iniciado
    assert monitoreo.sesion_iniciada is True

    # Verificamos que se haya habilitado el monitoreo
    assert interfaz.datos_guardados is True


# ============================================================
# PRUEBA 8 - SILENCIAR ALERTA
# ============================================================

def test_silenciar_alerta():
    """
    Verifica que el botón "Silenciar" llame correctamente
    a GestorAlertas.
    """

    gestor = GestorAlertasMock()

    interfaz = Interfaz(gestor_alertas=gestor)

    # Presionamos el botón Silenciar
    interfaz.silenciar_alerta()

    # Comprobamos que la alarma haya sido silenciada
    assert gestor.alerta_silenciada is True


# ============================================================
# PRUEBA 9 - MOSTRAR TEMPERATURA
# ============================================================

def test_mostrar_temp():
    """
    Verifica que mostrar_temp() obtenga la temperatura
    desde el Lector y la almacene en temp_actual.
    """

    # Creamos un lector que devuelve 17 °C
    lector = LectorMock(17)

    # Creamos la interfaz con ese lector
    interfaz = Interfaz(clase_lector=lector)

    # Pedimos la temperatura
    temperatura = interfaz.mostrar_temp()

    # Comprobamos el valor devuelto
    assert temperatura == 17.0

    # Comprobamos que también se haya actualizado temp_actual
    assert interfaz.temp_actual == 17.0

# PRUEBA 10 - LECTOR SIN NUEVA TEMPERATURA

def test_mostrar_temp_sin_dato():
    """
    Verifica que mostrar_temp() devuelva None cuando
    el Lector todavía no tenga una nueva temperatura.
    """

    # El lector no tiene una temperatura disponible
    lector = LectorMock(None)

    interfaz = Interfaz(clase_lector=lector)

    # Pedimos la temperatura
    temperatura = interfaz.mostrar_temp()

    # Debe devolver None
    assert temperatura is None

# PRUEBA 11 - FINALIZAR SESIÓN

def test_finalizar_sesion():
    """
    Verifica que finalizar_sesion() llame correctamente
    a finalizar_sesion() de Monitoreo.
    """

    monitoreo = MonitoreoMock()

    interfaz = Interfaz(monitoreo=monitoreo)

    # Finalizamos la sesión
    interfaz.finalizar_sesion()

    # Comprobamos que Monitoreo haya finalizado la sesión
    assert monitoreo.sesion_finalizada is True