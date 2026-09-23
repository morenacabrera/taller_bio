"""Clase lector"""

import serial
import time
 
 
class Lector:
    def __init__(self, puerto, velocidad):
        self.puerto = puerto
        self.velocidad = velocidad
        self._conexion = None  # acá se guarda el objeto Serial una vez conectado
 
    def conectar(self):
        """
        Abre la conexión serie con el Arduino.
        Devuelve True si se conectó correctamente, False si hubo un error.
        """
        try:
            self._conexion = serial.Serial(self.puerto, self.velocidad, timeout=1)
            time.sleep(2)  # el Arduino suele reiniciarse al abrir el puerto; le damos margen
            print(f"Conectado a {self.puerto} a {self.velocidad} baudios.")
            return True
        except serial.SerialException as e:
            print(f"Error al conectar con {self.puerto}: {e}")
            return False
 
    def leer_temperatura(self):
        """
        Lee una línea enviada por el Arduino y la interpreta como temperatura.
        Devuelve el valor como float, o None si la lectura falló o no era válida.
        """
        if self._conexion is None:
            print("No hay conexión activa. Llamá primero a conectar().")
            return None
 
        try:
            linea = self._conexion.readline().decode("utf-8").strip()
 
            if linea == "":
                return None  # no llegó nada en este ciclo
 
            # Acá se asume que el Arduino manda solo el número, ej: "15.3"
            # Si más adelante el Arduino manda también el estado de error
            # (ej: "15.3,OK" o "NAN,ERROR"), esta parte hay que adaptarla.
            temperatura = float(linea)
            return temperatura
 
        except ValueError:
            print(f"Dato inválido recibido: '{linea}'")
            return None
        except serial.SerialException as e:
            print(f"Error de comunicación: {e}")
            return None
 
    def desconectar(self):
        """Cierra la conexión serie de forma prolija."""
        if self._conexion is not None:
            self._conexion.close()
            print("Conexión cerrada.")
 
 
# --- Prueba manual de la clase ---
if __name__ == "__main__":
    lector = Lector(puerto="COM8", velocidad=9600)  # ajustá el puerto según tu PC
 
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