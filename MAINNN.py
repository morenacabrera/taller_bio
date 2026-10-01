"""
main.py — Punto de entrada del sistema de monitoreo de temperatura
del cuero cabelludo durante crioterapia capilar.
"""

import time
from clase_lector import Lector
from clase_interfaz import Interfaz

# Importación de clases restantes
from clase_gestor_alertas import Gestor_alertas
from clase_based_datos import BaseDeDatos
from Clase_monitoreo import Monitoreo

def main():
    gestor = None     # Instancia futura de Gestor_alertas()
    base_dato = None  # Instancia futura de Base_dato()
    monitoreo = None  # Instancia futura de Monitoreo()

    # Creamos el lector
    lector = Lector(puerto="COM3", velocidad=9600)
    
    # Creamos la interfaz pasándole el lector para que pueda capturar las temperaturas
    interfaz = Interfaz(monitoreo=monitoreo, gestor_alertas=gestor, clase_lector=lector)

    # --- 1. Conectar con el Arduino ---
    if not lector.conectar():
        interfaz.actualizar_estado_conexion(False)
        print("No se pudo conectar con el Arduino. Revisá el puerto y el cable.")
        return

    interfaz.actualizar_estado_conexion(True)
    print("Conexión establecida. Esperando a que ingreses los datos y presiones 'Guardar'...")

    # --- 2. Pausa de espera hasta que el usuario guarde los datos en la interfaz ---
    # El programa se queda congelado acá sin leer el sensor ni mostrar nada 
    # hasta que se toque el botón Guardar (que activa self.datos_guardados = True)
    while not getattr(interfaz, 'datos_guardados', False):
        time.sleep(0.5)

    print("¡Datos guardados! Iniciando el monitoreo de temperatura...")

    # --- 3. Ciclo principal de monitoreo ---
    try:
        while True:
            # La interfaz se encarga de pedir la temperatura al lector configurado
            temperatura = interfaz.mostrar_temp()

            if temperatura is not None:
                print(f"Temperatura actual: {temperatura:.1f} °C", flush=True)

                # Si el gestor de alertas está disponible, evaluamos
                if gestor is not None:
                    gestor.evaluar_temp(temperatura)

            time.sleep(1)  # Frecuencia de muestreo 1 Hz

    except KeyboardInterrupt:
        print("\nMonitoreo detenido manualmente.")
        interfaz.finalizar_sesion()

    finally:
        lector.desconectar()
        interfaz.actualizar_estado_conexion(False)


if __name__ == "__main__":
    main()