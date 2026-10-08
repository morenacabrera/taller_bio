import pytest
from unittest.mock import patch, MagicMock
import serial
import pytest
import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Importamos la clase Lector
from clase_lector import Lector


# ============================================================
# PRUEBA 1 - INICIALIZACIÓN
# ============================================================
def test_inicializacion_lector():
    """Verifica que el lector se inicialice con el puerto y velocidad correctos."""
    lector = Lector("COM3", 9600)
    
    assert lector.puerto == "COM3"
    assert lector.velocidad == 9600
    assert lector._conexion is None


# ============================================================
# PRUEBA 2 - CONEXIÓN EXITOSA
# ============================================================
@patch("clase_lector.serial.Serial")
def test_conectar_exitoso(mock_serial):
    """Verifica que conectar() abra el puerto serie correctamente y devuelva True."""
    # Configuramos el mock para que simule una conexión exitosa
    mock_conexion_instancia = MagicMock()
    mock_serial.return_value = mock_conexion_instancia

    lector = Lector("COM3", 9600)
    resultado = lector.conectar()

    # Comprobamos que se llamó a serial.Serial con los parámetros correctos
    mock_serial.assert_called_once_with("COM3", 9600, timeout=0.1)
    assert resultado is True
    assert lector._conexion == mock_conexion_instancia


# ============================================================
# PRUEBA 3 - ERROR DE CONEXIÓN
# ============================================================
@patch("clase_lector.serial.Serial")
def test_conectar_fallido(mock_serial):
    """Verifica que si ocurre un SerialException, conectar() devuelva False."""
    # Simulamos que al intentar conectar lanza una excepción
    mock_serial.side_effect = serial.SerialException("Puerto no disponible")

    lector = Lector("COM3", 9600)
    resultado = lector.conectar()

    assert resultado is False
    assert lector._conexion is None


# ============================================================
# PRUEBA 4 - LEER TEMPERATURA SIN CONEXIÓN
# ============================================================
def test_leer_temperatura_sin_conexion():
    """Verifica que leer_temperatura() devuelva None si no hay conexión activa."""
    lector = Lector("COM3", 9600)
    # No llamamos a conectar(), por lo que _conexion es None

    temperatura = lector.leer_temperatura()
    assert temperatura is None


# ============================================================
# PRUEBA 5 - LEER TEMPERATURA EXITOSAMENTE
# ============================================================
@patch("clase_lector.serial.Serial")
def test_leer_temperatura_exito(mock_serial):
    """Verifica que lea correctamente los datos del búfer y devuelva el float."""
    mock_conexion = MagicMock()
    mock_serial.return_value = mock_conexion

    lector = Lector("COM3", 9600)
    lector.conectar()

    # Simulamos que hay datos en el búfer
    mock_conexion.in_waiting = 5
    # Simulamos que el puerto devuelve una línea con la temperatura
    mock_conexion.read.return_value = b"23.5\n"

    temperatura = lector.leer_temperatura()

    assert temperatura == 23.5
    mock_conexion.read.assert_called_once_with(5)


# ============================================================
# PRUEBA 6 - LEER TEMPERATURA CON LÍNEAS INVÁLIDAS O VACÍAS
# ============================================================
@patch("clase_lector.serial.Serial")
def test_leer_temperatura_ignora_invalidos(mock_serial):
    """Verifica que busque el último valor válido descartando texto o líneas vacías."""
    mock_conexion = MagicMock()
    mock_serial.return_value = mock_conexion

    lector = Lector("COM3", 9600)
    lector.conectar()

    mock_conexion.in_waiting = 15
    # Enviamos texto basura y luego una temperatura válida al final
    mock_conexion.read.return_value = b"Iniciando...\n\n18.2\n"

    temperatura = lector.leer_temperatura()

    assert temperatura == 18.2


# ============================================================
# PRUEBA 7 - DESCONECTAR
# ============================================================
@patch("clase_lector.serial.Serial")
def test_desconectar(mock_serial):
    """Verifica que desconectar() cierre la conexión serie adecuadamente."""
    mock_conexion = MagicMock()
    mock_serial.return_value = mock_conexion

    lector = Lector("COM3", 9600)
    lector.conectar()

    lector.desconectar()

    mock_conexion.close.assert_called_once()
    assert lector._conexion is None
if __name__ == '__main__':
    unittest.main()