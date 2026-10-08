import unittest
import sys
import os
from datetime import datetime

# Agregamos la carpeta padre al PYTHONPATH para encontrar las clases principales
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clase_monitoreo import Monitoreo

class TestMonitoreo(unittest.TestCase):

    def setUp(self):
        """Se ejecuta antes de cada prueba. Instancia un nuevo objeto Monitoreo."""
        self.monitoreo = Monitoreo()

    def test_estado_inicial(self):
        """Verifica que al instanciar, los atributos comiencen en None o vacíos."""
        self.assertIsNone(self.monitoreo.numero_gorra)
        self.assertIsNone(self.monitoreo.tiempo_inicio)
        self.assertIsNone(self.monitoreo.tiempo_fin)

    def test_iniciar_sesion(self):
        """Verifica que iniciar sesión asigne el número de gorra y guarde el tiempo de inicio."""
        num_gorra_prueba = 3
        self.monitoreo.iniciar_sesion(num_gorra_prueba)

        self.assertEqual(self.monitoreo.numero_gorra, num_gorra_prueba)
        self.assertIsNotNone(self.monitoreo.tiempo_inicio)
        self.assertIsInstance(self.monitoreo.tiempo_inicio, datetime)
        # El tiempo de fin debe seguir siendo None al iniciar
        self.assertIsNone(self.monitoreo.tiempo_fin)

    def test_finalizar_sesion(self):
        """Verifica que al finalizar la sesión se registre el tiempo de fin correctamente."""
        self.monitoreo.iniciar_sesion(1)
        
        # Simulamos un pequeño delay o simplemente finalizamos
        self.monitoreo.finalizar_sesion()

        self.assertIsNotNone(self.monitoreo.tiempo_fin)
        self.assertIsInstance(self.monitoreo.tiempo_fin, datetime)
        
        # Comprobamos que el tiempo de fin sea posterior o igual al de inicio
        self.assertGreaterEqual(self.monitoreo.tiempo_fin, self.monitoreo.tiempo_inicio)

if __name__ == '__main__':
    unittest.main()