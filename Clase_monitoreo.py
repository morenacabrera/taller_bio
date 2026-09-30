"""Clase Monitoreo"""
from datetime import datetime


class Monitoreo:
    def __init__(self):
        self.numero_gorra = None      # (antes: num_gorra; unificado con iniciar_sesion)
        self.tiempo_inicio = None
        self.tiempo_fin = None

    def iniciar_sesion(self, num_gorra):
        self.numero_gorra = num_gorra
        self.tiempo_inicio = datetime.now()
        self.tiempo_fin = None

    def finalizar_sesion(self):
        # Se ejecuta cuando el usuario presiona el botón "Finalizar"
        self.tiempo_fin = datetime.now()


# --- Pruebas: ahora SOLO corren si ejecutás este archivo directamente ---
if __name__ == "__main__":
    monitoreo = Monitoreo()
    monitoreo.iniciar_sesion(1)
    monitoreo.finalizar_sesion()

    print(monitoreo.tiempo_inicio.strftime("La sesión inició el %d/%m a las %H:%M:%S"))
    print(monitoreo.tiempo_fin.strftime("La sesión finalizó el %d/%m a las %H:%M:%S"))