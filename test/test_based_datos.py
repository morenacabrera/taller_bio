import unittest
import os
import sys

# Agregamos la carpeta padre al PYTHONPATH para que encuentre las clases principales
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clase_based_datos import BaseDeDatos

class TestBaseDeDatos(unittest.TestCase):
    
    def setUp(self):
        """Se ejecuta antes de cada prueba. Crea una base de datos temporal."""
        self.nombre_db_prueba = "test_crioterapia.db"
        if os.path.exists(self.nombre_db_prueba):
            os.remove(self.nombre_db_prueba)
        
        self.db = BaseDeDatos(nombre_db=self.nombre_db_prueba)

    def tearDown(self):
        """Se ejecuta al terminar cada prueba. Borra la base de datos temporal."""
        if os.path.exists(self.nombre_db_prueba):
            os.remove(self.nombre_db_prueba)

    def test_inicializacion_tabla(self):
        """Verifica que la base de datos cree la tabla 'tratamientos' correctamente."""
        conexion = self.db.conectar()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tratamientos';")
        tabla = cursor.fetchone()
        conexion.close()
        
        self.assertIsNotNone(tabla, "La tabla 'tratamientos' no fue creada en la base de datos.")
        self.assertEqual(tabla[0], 'tratamientos')

    def test_guardar_tratamiento(self):
        """Verifica que un diccionario de datos se guarde e inserte correctamente."""
        datos_prueba = {
            'id_paciente': 'P12345',
            'num_sesion': 1,
            'num_gorro': 2,
            'temp_min_umbral': 2.0,
            'temp_max_umbral': 10.0,
            'temp_inicial': 15.5,
            'temp_final': 4.1,
            'temp_promedio': 7.8,
            'veces_fuera_rango': 3,
            'alertas_silenciadas': 1,
            'hora_inicio': '10:00:00',
            'hora_fin': '10:30:00',
            'fecha': '2026-06-06'
        }

        self.db.guardar_tratamiento(datos_prueba)

        conexion = self.db.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM tratamientos;")
        resultado = cursor.fetchone()
        conexion.close()

        self.assertIsNotNone(resultado, "No se encontró ningún registro en la tabla tratamientos.")
        self.assertEqual(resultado[1], 'P12345')
        self.assertEqual(resultado[2], 1)
        self.assertEqual(resultado[3], 2)
        self.assertEqual(resultado[5], 10.0)
        self.assertEqual(resultado[8], 7.8)

if __name__ == '__main__':
    unittest.main()