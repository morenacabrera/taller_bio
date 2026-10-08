import unittest
import sys
import os

# Agregamos la carpeta padre al PYTHONPATH para encontrar las clases principales
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clase_gestor_alertas import Gestor_alertas

class TestGestorAlertas(unittest.TestCase):

    def setUp(self):
        """Se ejecuta antes de cada prueba. Instancia un nuevo gestor."""
        self.gestor = Gestor_alertas()

    def test_umbrales_no_definidos(self):
        """Verifica que si los umbrales son None, la alerta siempre devuelva False."""
        self.gestor.umbral_min = None
        self.gestor.umbral_max = None
        
        resultado = self.gestor.evaluar_temp(15.0)
        self.assertFalse(resultado)
        self.assertFalse(self.gestor.alerta_activa)

    def test_temperatura_dentro_de_rango(self):
        """Verifica que una temperatura dentro del rango no active alertas."""
        self.gestor.umbral_min = 10.0
        self.gestor.umbral_max = 20.0

        resultado = self.gestor.evaluar_temp(15.0)
        self.assertFalse(resultado)
        self.assertFalse(self.gestor.alerta_activa)

    def test_temperatura_muy_baja_activa_alerta(self):
        """Verifica que una temperatura menor al umbral mínimo active la alerta."""
        self.gestor.umbral_min = 10.0
        self.gestor.umbral_max = 20.0

        resultado = self.gestor.evaluar_temp(5.0) # Demasiado frío
        self.assertTrue(resultado)
        self.assertTrue(self.gestor.alerta_activa)

    def test_temperatura_muy_alta_activa_alerta(self):
        """Verifica que una temperatura mayor al umbral máximo active la alerta."""
        self.gestor.umbral_min = 10.0
        self.gestor.umbral_max = 20.0

        resultado = self.gestor.evaluar_temp(25.0) # Demasiado caliente
        self.assertTrue(resultado)
        self.assertTrue(self.gestor.alerta_activa)

    def test_silenciar_alerta(self):
        """Verifica que al silenciar la alerta, eval_temp devuelva False aunque siga fuera de rango."""
        self.gestor.umbral_min = 10.0
        self.gestor.umbral_max = 20.0

        # Disparamos alerta primero
        self.gestor.evaluar_temp(5.0)
        self.assertTrue(self.gestor.alerta_activa)

        # Silenciamos
        self.gestor.silenciar_alerta()
        self.assertFalse(self.gestor.alerta_activa)
        self.assertTrue(self.gestor._silenciada)

        # Evaluamos de nuevo con la misma temperatura fuera de rango -> no debe sonar
        resultado_silenciado = self.gestor.evaluar_temp(5.0)
        self.assertFalse(resultado_silenciado)

    def test_rearme_automatico_al_volver_a_rango(self):
        """Verifica que cuando la temperatura vuelve al rango, el sistema se rearma."""
        self.gestor.umbral_min = 10.0
        self.gestor.umbral_max = 20.0

        # Disparamos y silenciamos
        self.gestor.evaluar_temp(5.0)
        self.gestor.silenciar_alerta()

        # La temperatura vuelve a la normalidad
        self.gestor.evaluar_temp(15.0)
        self.assertFalse(self.gestor._silenciada)
        self.assertFalse(self.gestor.alerta_activa)

        # Si vuelve a irse de rango después de haberse normalizado, debe sonar otra vez
        resultado_nuevo = self.gestor.evaluar_temp(25.0)
        self.assertTrue(resultado_nuevo)
        self.assertTrue(self.gestor.alerta_activa)

if __name__ == '__main__':
    unittest.main()