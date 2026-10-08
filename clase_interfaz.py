"""
interfaz.py — Clase Interfaz para el Monitoreo de Crioterapia Capilar.

Puente entre la pantalla y el resto de las clases:
- Monitoreo (sesión y tiempos)
- Gestor_alertas (umbrales y silenciar)
- Lector (temperatura)
- Base_dato (pendiente)
"""


class Interfaz:
    def __init__(self, monitoreo=None, gestor_alertas=None, clase_lector=None):
        self.monitoreo = monitoreo
        self.gestor_alertas = gestor_alertas
        self.clase_lector = clase_lector
        self.estado_conexion: str = "DESCONECTADO"
        self.temp_actual: float = 0.0

    def actualizar_estado_conexion(self, conectado: bool):
        """Actualiza el estado de la conexión en la interfaz."""
        self.estado_conexion = "CONECTADO" if conectado else "DESCONECTADO"
        print(f"[INTERFAZ] Estado de conexión: {self.estado_conexion}")

    def configurar_umbrales(self, temp_min, temp_max):
        """Pantalla: 'INGRESE EL RANGO TERMICO' -> guarda umbral_min y umbral_max en Gestor_alertas."""
        temp_min = float(temp_min)
        temp_max = float(temp_max)
        if temp_min >= temp_max:
            raise ValueError("La temperatura mínima debe ser menor que la máxima.")

        if self.gestor_alertas is not None:
            self.gestor_alertas.umbral_min = temp_min
            self.gestor_alertas.umbral_max = temp_max
        print(f"[INTERFAZ] Rango térmico configurado: [{temp_min} °C - {temp_max} °C]")

    def registrar_paciente(self, id_paciente, num_sesion):
        if hasattr(self, 'base_dato') and self.base_dato is not None:
             self.base_dato.guardar_paciente(id_paciente, num_sesion)
        print(f"[INTERFAZ] Paciente registrado: ID = {id_paciente}, Sesión N° = {num_sesion}")

    def registrar_gorra(self, num_gorro):
        """Número de gorra -> Monitoreo (inicia la sesión)."""
        if self.monitoreo is not None:
            self.monitoreo.iniciar_sesion(num_gorro)
            print(f"[INTERFAZ] Gorra N° {num_gorro} registrada.")

    def al_presionar_guardar(self, id_paciente, num_sesion, num_gorro):
        """
        Acción al presionar el botón 'Guardar' en la interfaz:
        1. Registra los datos del paciente.
        2. Registra la gorra e inicia la sesión en el módulo de monitoreo.
        3. Activa la bandera que permite que el sistema principal comience a medir.
        """
        # Ejecutamos los registros de manera unificada
        self.registrar_paciente(id_paciente, num_sesion)
        self.registrar_gorra(num_gorro)
        
        # Desbloqueamos el ciclo principal de mediciones
        self.datos_guardados = True
        print("[INTERFAZ] ¡Datos guardados con éxito! Habilitando el monitoreo térmico...")

    def silenciar_alerta(self):
        """Botón 'Silenciar' -> Gestor_alertas."""
        print("[INTERFAZ] Botón 'Silenciar' presionado.")
        if self.gestor_alertas is not None:
            self.gestor_alertas.silenciar_alerta()

    def mostrar_temp(self):
        """
        Pantalla: 'TEMPERATURA ACTUAL'. Pide la temperatura al Lector.
        Devuelve un float, o None si todavía no llegó un dato nuevo del Arduino
        (en ese caso temp_actual conserva el último valor).
        """
        if self.clase_lector is None:
            return None

        temperatura = self.clase_lector.leer_temperatura()
        if temperatura is None:
            return None

        self.temp_actual = float(temperatura)
        return self.temp_actual

    def finalizar_sesion(self):
        """Botón 'Finalizar' -> Monitoreo registra tiempo_fin."""
        print("[INTERFAZ] Botón 'Finalizar' presionado. Concluyendo sesion...")
        if self.monitoreo is not None:
            self.monitoreo.finalizar_sesion()
