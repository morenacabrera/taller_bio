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

# TODO: descomentar a medida que se vayan creando estos archivos
# from gestor_alertas import Gestor_alertas
# from base_dato import Base_dato
# from interfaz import Interfaz
# from monitoreo import Monitoreo


def main():
    # --- 1. Crear los objetos principales ---
    lector = Lector(puerto="COM8", velocidad=9600)  # ajustar puerto según la PC

    # TODO: crear el resto de los objetos
    # gestor = Gestor_alertas()
    # base_dato = Base_dato()
    # interfaz = Interfaz(gestor, base_dato)  # la interfaz necesita hablarles a ambas
    # monitoreo = Monitoreo()

    # --- 2. Conectar con el Arduino ---
    if not lector.conectar():
        print("No se pudo conectar con el Arduino. Revisá el puerto y el cable.")
        return

    # TODO: acá iría, por ejemplo, registrar_paciente() y registrar_gorra()
    # desde la interfaz, antes de arrancar el monitoreo continuo.
    # interfaz.registrar_paciente()
    # interfaz.registrar_gorra()

    # --- 3. Ciclo principal de monitoreo ---
    try:
        while True:
            temperatura = lector.leer_temperatura()

            if temperatura is not None:
                print(f"Temperatura actual: {temperatura} °C")

                # TODO: una vez que exista Gestor_alertas, acá se evaluaría:
                # gestor.evaluar_temp(temperatura)

                # TODO: y una vez que exista Interfaz, acá se mostraría:
                # interfaz.mostrar_temp(temperatura)

            time.sleep(1)  # respeta la frecuencia de muestreo de 1 Hz

    except KeyboardInterrupt:
        print("\nMonitoreo detenido por el usuario.")

    finally:
        lector.desconectar()


if __name__ == "__main__":
    main()