"""
main.py — Punto de entrada del sistema de monitoreo de temperatura
del cuero cabelludo durante crioterapia capilar.

Acá se crean los objetos de cada clase y se arranca el ciclo principal
del programa. A medida que se vayan programando las clases restantes
(Gestor_alertas, Base_dato, Interfaz, Monitoreo), hay que ir
descomentando e integrando las partes marcadas con TODO.
"""

import time
from clase_lector import Lector
from clase_interfaz import Interfaz

# TODO: Descomentar a medida que implementen las clases faltantes
# from gestor_alertas import Gestor_alertas
# from base_dato import Base_dato
# from monitoreo import Monitoreo


def main():
    # --- 1. Crear objetos de soporte / referencias vacías por ahora ---
    gestor = None     # Instancia futura de Gestor_alertas()
    base_dato = None  # Instancia futura de Base_dato()
    monitoreo = None  # Instancia futura de Monitoreo()

    # --- 2. Crear el lector y la interfaz ---
    lector = Lector(puerto="COM3", velocidad=9600)  # Ajustar el puerto según la PC
    interfaz = Interfaz(monitoreo=monitoreo, gestor_alertas=gestor, base_dato=base_dato)

    # --- 3. Conectar con el Arduino ---
    if not lector.conectar():
        interfaz.actualizar_estado_conexion(False)
        print("No se pudo conectar con el Arduino. Revisá el puerto y el cable.")
        return

    interfaz.actualizar_estado_conexion(True)

    # --- 4. Carga inicial de datos (Simulación del ingreso en pantalla) ---
    # En una GUI real estos métodos se ejecutan cuando el usuario presiona "GUARDAR"
    interfaz.registrar_paciente(id_paciente="PAC-104", num_sesion=3)
    interfaz.registrar_gorra(num_gorro=8)
    interfaz.configurar_umbrales(temp_min=10.0, temp_max=18.0)

    # --- 5. Ciclo principal de monitoreo ---
    try:
        while True:
            temperatura = lector.leer_temperatura()

            if temperatura is not None:
                # Actualiza y muestra la temperatura en la Interfaz
                interfaz.mostrar_temp(temperatura)

                # Si el gestor de alertas está disponible, evaluamos
                if gestor is not None:
                    gestor.evaluar_temp(temperatura)

            time.sleep(1)  # Frecuencia de muestreo 1 Hz

    except KeyboardInterrupt:
        print("\nMonitoreo detenido manualmente.")
        interfaz.finalizar_tratamiento()

    finally:
        lector.desconectar()
        interfaz.actualizar_estado_conexion(False)


if __name__ == "__main__":
    main()