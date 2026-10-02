import sqlite3
from datetime import datetime

class BaseDeDatos:
    def __init__(self, nombre_db = "crioterapia.db"):
        self.nombre_db = nombre_db
        self.inicializar_base()

    def conectar(self):
        return sqlite3.connect(self.nombre_db)

    def inicializar_base(self):
        """Crea la tabla de tratamientos si no existe."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tratamientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_paciente TEXT,
                num_sesion INTEGER,
                num_gorro INTEGER,
                temp_min_umbral REAL,
                temp_max_umbral REAL,
                temp_inicial REAL,
                temp_final REAL,
                temp_promedio REAL,
                veces_fuera_rango INTEGER,
                alertas_silenciadas INTEGER,
                hora_inicio TEXT,
                hora_fin TEXT,
                fecha TEXT
            )
        """)
        conexion.commit()
        conexion.close()

    def guardar_tratamiento(self, datos):
        """Inserta un registro completo del tratamiento en la base de datos."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        cursor.execute("""
            INSERT INTO tratamientos (
                id_paciente, num_sesion, num_gorro, 
                temp_min_umbral, temp_max_umbral, 
                temp_inicial, temp_final, temp_promedio, 
                veces_fuera_rango, alertas_silenciadas, 
                hora_inicio, hora_fin, fecha
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos.get('id_paciente'),
            datos.get('num_sesion'),
            datos.get('num_gorro'),
            datos.get('temp_min_umbral'),
            datos.get('temp_max_umbral'),
            datos.get('temp_inicial'),
            datos.get('temp_final'),
            datos.get('temp_promedio'),
            datos.get('veces_fuera_rango'),
            datos.get('alertas_silenciadas'),
            datos.get('hora_inicio'),
            datos.get('hora_fin'),
            datos.get('fecha')
        ))
        
        conexion.commit()
        conexion.close()
        print("[BD] Tratamiento guardado exitosamente en la base de datos.")