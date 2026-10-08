"""Clase Gestor_alertas"""


class Gestor_alertas:
    def __init__(self):
        self.umbral_min = None
        self.umbral_max = None
        self.alerta_activa = False
        self._silenciada = False   # recuerda si el usuario ya apretó "Silenciar"

    def evaluar_temp(self, temperatura):
        """
        Compara la temperatura contra los umbrales (umbral_min / umbral_max).
        Devuelve True si hay una alerta activa y sin silenciar.
        """
        if self.umbral_min is None or self.umbral_max is None:
            self.alerta_activa = False
            return False

        fuera_de_rango = temperatura < self.umbral_min or temperatura > self.umbral_max

        if fuera_de_rango:
            # Si ya se silenció, sigue fuera de rango pero no vuelve a sonar
            if not self._silenciada:
                if not self.alerta_activa:
                    print(f"¡ALERTA! Temperatura fuera de rango: {temperatura}°C")
                self.alerta_activa = True
        else:
            # Volvió al rango: se rearma para la próxima vez
            self._silenciada = False
            self.alerta_activa = False

        return self.alerta_activa

    def silenciar_alerta(self):
        """
        Apaga el aviso sin interrumpir el monitoreo. No vuelve a sonar hasta que
        la temperatura regrese al rango y se salga de nuevo.
        """
        self._silenciada = True
        self.alerta_activa = False
        print("Alerta silenciada. El monitoreo continúa.")