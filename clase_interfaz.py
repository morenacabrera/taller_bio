"""
interfaz.py — Clase Interfaz para el Monitoreo de Crioterapia Capilar.

Esta clase actúa como puente entre la pantalla (GUI) y el resto de las clases del sistema:
- Monitoreo (para registrar sesión e inicio de tiempo)
- Gestor_alertas (para configurar umbrales y silenciar)
- Base_dato (para persistir datos del paciente y eventos)
"""

class Interfaz:
    def __init__(self, monitoreo=None, gestor_alertas=None, base_dato=None):
        """
        Inicializa la interfaz relacionándola con los demás módulos del sistema.
        Se pueden pasar instancias reales o 'None' (para desarrollo gradual).
        """
        # Relaciones según el UML
        self.monitoreo = monitoreo
        self.gestor_alertas = gestor_alertas
        self.base_dato = base_dato

        # Atributo definido en el UML
        self.temp_actual: float = 0.0

        # Atributos derivados de la interfaz gráfica dibujada
        self.id_paciente: str = ""
        self.num_sesion: int = 0
        self.num_gorro: int = 0
        self.temp_min: float = 0.0
        self.temp_max: float = 0.0
        self.estado_conexion: str = "DESCONECTADO"

    # ------------------------------------------------------------------
    # Métodos del UML y relación con la pantalla
    # ------------------------------------------------------------------

    def registrar_paciente(self, id_paciente: str, num_sesion: int):
        """
        Relacionado con la pantalla: 'INGRESE LOS SIGUIENTES DATOS' -> ID y N° de sesión.
        Guarda los datos del paciente en la interfaz.
        """
        self.id_paciente = str(id_paciente)
        self.num_sesion = int(num_sesion)
        print(f"[INTERFAZ] Paciente registrado: ID = {self.id_paciente}, Sesión N° = {self.num_sesion}")

    def registrar_gorra(self, num_gorro: int):
        """
        Relacionado con la pantalla: 'N° de Gorro' -> Botón GUARDAR.
        Conecta con:
        1. Monitoreo.iniciar_sesion(num_gorra)
        2. Base_dato.guardar_paciente(...)
        """
        self.num_gorro = int(num_gorro)
        print(f"[INTERFAZ] Gorra N° {self.num_gorro} registrada.")

        # Transmite a la clase Monitoreo si existe
        if self.monitoreo is not None:
            self.monitoreo.iniciar_sesion(self.num_gorro)

        # Guarda la ficha del paciente/sesión en la Base de datos si existe
        if self.base_dato is not None:
            self.base_dato.guardar_paciente(self.id_paciente, self.num_sesion, self.num_gorro)

    def configurar_umbrales(self, temp_min: float, temp_max: float):
        """
        Relacionado con la pantalla: 'INGRESE EL RANGO TERMICO' -> Temp. máx, Temp. mín -> Botón GUARDAR.
        Conecta con: Gestor_alertas (actualiza umbral_min y umbral_max).
        """
        self.temp_min = float(temp_min)
        self.temp_max = float(temp_max)

        # Transmite los umbrales al Gestor de alertas
        if self.gestor_alertas is not None:
            self.gestor_alertas.umbral_min = self.temp_min
            self.gestor_alertas.umbral_max = self.temp_max

        print(f"[INTERFAZ] Rango térmico configurado: [{self.temp_min} °C - {self.temp_max} °C]")

    def mostrar_temp(self, temperatura: float = None):
        """
        Relacionado con la pantalla: 'TEMPERATURA ACTUAL: ______ [°C]'.
        Muestra en pantalla el valor leído en tiempo real desde el Lector.
        """
        if temperatura is not None:
            self.temp_actual = float(temperatura)

        print(f"[PANTALLA] TEMPERATURA ACTUAL: {self.temp_actual:.1f} °C")

    # ------------------------------------------------------------------
    # Botones de Acción de la pantalla de Avisos
    # ------------------------------------------------------------------

    def silenciar_alerta(self):
        """
        Relacionado con la pantalla: Botón 'SILENCIAR' en el recuadro AVISOS.
        Conecta con: Gestor_alertas.silenciar_alerta()
        """
        print("[INTERFAZ] Botón 'SILENCIAR' presionado.")
        if self.gestor_alertas is not None:
            self.gestor_alertas.silenciar_alerta()

    def finalizar_tratamiento(self):
        """
        Relacionado con la pantalla: Botón 'FINALIZAR' en el recuadro AVISOS.
        Conecta con: Base_dato.guardar_evento(...) para registrar la salida/cierre.
        """
        print("[INTERFAZ] Botón 'FINALIZAR' presionado. Concluyendo sesión...")
        if self.base_dato is not None:
            self.base_dato.guardar_evento(
                num_gorra=self.num_gorro,
                temp=self.temp_actual,
                mensaje="Tratamiento Finalizado por Operador"
            )

    def actualizar_estado_conexion(self, conectado: bool):
        """
        Relacionado con la pantalla: 'ESTADO DE CONEXION: CONECTADO / DESCONECTADO'.
        """
        self.estado_conexion = "CONECTADO" if conectado else "DESCONECTADO"
        print(f"[PANTALLA] ESTADO DE CONEXIÓN: {self.estado_conexion}")