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
            self._conexion = serial.Serial(self.puerto, self.velocidad, timeout=1)
            print(f"Conectado a {self.puerto} a {self.velocidad} baudios.")
            return True
        except serial.SerialException as e:
            print(f"Error al conectar con {self.puerto}: {e}")
            self._conexion = None
            return False

    def leer_temperatura(self):
        """
        Devuelve la última temperatura recibida (float) o None si no hay dato nuevo.
        Si se pierde la conexión (cable desenchufado) lanza la excepción para que
        app.py reconecte.
        """
        if self._conexion is None:
            print("No hay conexión activa. Llamá primero a conectar().")
            return None

        linea = None
        try:
            # Si hay varias líneas acumuladas, nos quedamos con la más reciente
            while self._conexion.in_waiting > 0:
                linea = self._conexion.readline().decode("utf-8", errors="ignore").strip()

            if linea is None or linea == "":
                return None

            return float(linea)

        except ValueError:
            print(f"Dato inválido recibido: '{linea}'")
            return None
        except serial.SerialException as e:
            print(f"Error de comunicación: {e}")
            raise   # app.py lo captura, cierra y reconecta

    def desconectar(self):
        """Cierra la conexión serie."""
        if self._conexion is not None:
            try:
                self._conexion.close()
            except Exception:
                pass
            self._conexion = None
            print("Conexión cerrada.")


# Prueba manual de la clase
if __name__ == "__main__":
    lector = Lector(puerto="COM8", velocidad=9600)

    if lector.conectar():
        try:
            while True:
                temp = lector.leer_temperatura()
                if temp is not None:
                    print(f"Temperatura recibida: {temp} °C")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nDeteniendo lectura...")
        finally:
            lector.desconectar()