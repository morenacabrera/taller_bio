import pytest
import sys
import os
import unittest
# Agrega la carpeta principal al path de búsqueda
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clase_interfaz import Interfaz


# ============================================================
# OBJETOS SIMULADOS (MOCKS)
# ============================================================

class GestorAlertasMock:
    def __init__(self):
        self.umbral_min = None
        self.umbral_max = None
        self.alerta_silenciada = False

    def silenciar_alerta(self):
        self.alerta_silenciada = True


class MonitoreoMock:
    def __init__(self):
        self.gorra = None
        self.sesion_iniciada = False
        self.sesion_finalizada = False

    def iniciar_sesion(self, num_gorro):
        self.gorra = num_gorro
        self.sesion_iniciada = True

    def finalizar_sesion(self):
        self.sesion_finalizada = True


class LectorMock:
    def __init__(self, temperatura=None):
        self.temperatura = temperatura

    def leer_temperatura(self):
        return self.temperatura


class BaseDatosMock:
    def __init__(self):
        self.paciente = None

    def guardar_paciente(self, id_paciente, num_sesion):
        self.paciente = (id_paciente, num_sesion)


# ============================================================
# PRUEBAS UNITARIAS
# ============================================================

def test_inicializacion_interfaz():
    interfaz = Interfaz()
    assert interfaz.estado_conexion == "DESCONECTADO"
    assert interfaz.temp_actual == 0.0
    assert interfaz.monitoreo is None
    assert interfaz.gestor_alertas is None
    assert interfaz.clase_lector is None


def test_actualizar_estado_conexion():
    interfaz = Interfaz()
    
    interfaz.actualizar_estado_conexion(True)
    assert interfaz.estado_conexion == "CONECTADO"

    interfaz.actualizar_estado_conexion(False)
    assert interfaz.estado_conexion == "DESCONECTADO"


def test_configurar_umbrales():
    gestor = GestorAlertasMock()
    interfaz = Interfaz(gestor_alertas=gestor)
    
    interfaz.configurar_umbrales("15", "18")  # Prueba conversión desde string/float
    assert gestor.umbral_min == 15.0
    assert gestor.umbral_max == 18.0


def test_configurar_umbrales_sin_gestor():
    interfaz = Interfaz(gestor_alertas=None)
    # No debería explotar si gestor_alertas es None
    interfaz.configurar_umbrales(10, 20)


def test_configurar_umbrales_invalidos():
    gestor = GestorAlertasMock()
    interfaz = Interfaz(gestor_alertas=gestor)
    
    with pytest.raises(ValueError):
        interfaz.configurar_umbrales(20, 18)


def test_registrar_paciente_sin_base_datos():
    interfaz = Interfaz()
    # No tiene el atributo base_dato, no debe fallar
    interfaz.registrar_paciente(123, 1)


def test_registrar_paciente_con_base_datos():
    base_datos = BaseDatosMock()
    interfaz = Interfaz()
    interfaz.base_dato = base_datos
    
    interfaz.registrar_paciente(456, 3)
    assert base_datos.paciente == (456, 3)


def test_registrar_gorra():
    monitoreo = MonitoreoMock()
    interfaz = Interfaz(monitoreo=monitoreo)
    
    interfaz.registrar_gorra(2)
    assert monitoreo.gorra == 2
    assert monitoreo.sesion_iniciada is True


def test_registrar_gorra_sin_monitoreo():
    interfaz = Interfaz(monitoreo=None)
    interfaz.registrar_gorra(2)  # No debe fallar


def test_al_presionar_guardar():
    base_datos = BaseDatosMock()
    monitoreo = MonitoreoMock()
    interfaz = Interfaz(monitoreo=monitoreo)
    interfaz.base_dato = base_datos

    interfaz.al_presionar_guardar(id_paciente=789, num_sesion=1, num_gorro=4)

    assert base_datos.paciente == (789, 1)
    assert monitoreo.gorra == 4
    assert monitoreo.sesion_iniciada is True
    assert interfaz.datos_guardados is True


def test_silenciar_alerta():
    gestor = GestorAlertasMock()
    interfaz = Interfaz(gestor_alertas=gestor)
    
    interfaz.silenciar_alerta()
    assert gestor.alerta_silenciada is True


def test_silenciar_alerta_sin_gestor():
    interfaz = Interfaz(gestor_alertas=None)
    interfaz.silenciar_alerta()  # No debe fallar


def test_mostrar_temp_sin_lector():
    interfaz = Interfaz(clase_lector=None)
    assert interfaz.mostrar_temp() is None


def test_mostrar_temp_exito():
    lector = LectorMock(21.5)
    interfaz = Interfaz(clase_lector=lector)

    temp = interfaz.mostrar_temp()
    assert temp == 21.5
    assert interfaz.temp_actual == 21.5


def test_mostrar_temp_lector_none():
    lector = LectorMock(None)
    interfaz = Interfaz(clase_lector=lector)

    assert interfaz.mostrar_temp() is None


def test_finalizar_sesion():
    monitoreo = MonitoreoMock()
    interfaz = Interfaz(monitoreo=monitoreo)

    interfaz.finalizar_sesion()
    assert monitoreo.sesion_finalizada is True


def test_finalizar_sesion_sin_monitoreo():
    interfaz = Interfaz(monitoreo=None)
    interfaz.finalizar_sesion()  # No debe fallar
if __name__ == '__main__':
    unittest.main()