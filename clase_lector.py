"""Clase Lector"""

import serial
import time


class Lector:
    def __init__(self, puerto, velocidad):
        self.puerto = puerto
        self.velocidad = velocidad
        self._conexion = None

    def conectar(self):
        """Abre la conexión serie. Devuelve True si se conectó, False si falló."""
        try:
            # Timeout corto para evitar bloqueos y mejorar la fluidez
            self._conexion = serial.Serial(self.puerto, self.velocidad, timeout=0.1)
            print(f"Conectado a {self.puerto} a {self.velocidad} baudios.")
            return True
        except serial.SerialException as e:
            print(f"Error al conectar con {self.puerto}: {e}")
            self._conexion = None
            return False

    def leer_temperatura(self):
        """
        Lee instantáneamente el búfer serie y devuelve la temperatura más reciente (float)
        o None si no hay datos nuevos, evitando el retraso (lag) por acumulación.
        """
        if self._conexion is None:
            print("No hay conexión activa. Llamá primero a conectar().")
            return None

        try:
            if self._conexion.in_waiting > 0:
                # Lee todo lo acumulado en el búfer de una sola vez
                datos_bytes = self._conexion.read(self._conexion.in_waiting)
                texto = datos_bytes.decode("utf-8", errors="ignore")
                
                # Separar por líneas
                lineas = texto.splitlines()
                
                # Recorrer desde el final para buscar el último valor numérico válido (el más actual)
                for linea in reversed(lineas):
                    linea = linea.strip()
                    if linea:
                        try:
                            return float(linea)
                        except ValueError:
                            continue
            
            return None

        except serial.SerialException as e:
            print(f"Error de comunicación: {e}")
            raise  # app.py lo captura, cierra y reconecta

    def desconectar(self):
        """Cierra la conexión serie."""
        if self._conexion is not None:
            try:
                self._conexion.close()
            except Exception:
                pass
            self._conexion = None
            print("Conexión cerrada.")

