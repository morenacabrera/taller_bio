"""
app.py — Servidor Web y Monitoreo en Tiempo Real.
"""

import logging
import threading
import time
from clase_interfaz import Interfaz
from clase_lector import Lector
from clase_gestor_alertas import Gestor_alertas
# from clase_base_dato import Base_dato
from Clase_monitoreo import Monitoreo
from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder=".")

# Oculta las líneas "GET /api/obtener_estado ..." para que se vea la temperatura en la terminal
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# --- Configuración de puerto ---
PUERTO = "COM8"
VELOCIDAD = 9600

# --- Instancias reales de cada clase ---
lector = Lector(puerto=PUERTO, velocidad=VELOCIDAD)
gestor = Gestor_alertas()
# base_dato = Base_dato()
monitoreo = Monitoreo()

interfaz = Interfaz(monitoreo=monitoreo, gestor_alertas=gestor, clase_lector=lector)  # base_dato=base_dato)

# --- Estado compartido ---
monitoreo_activo = False
conexion_activa = False
alerta_activa = False
temp_actual = None          # última temperatura leída (siempre se actualiza)


def ciclo_monitoreo():
    """Lee el Arduino todo el tiempo. Reconecta solo si se cae."""
    global monitoreo_activo, conexion_activa, alerta_activa, temp_actual

    while True:
        # 1) Conectar (reintenta hasta lograrlo)
        while not conexion_activa:
            conexion_activa = lector.conectar()
            if not conexion_activa:
                print("No se pudo conectar. Reintentando en 3 segundos...")
                time.sleep(3)

        # 2) Leer y mostrar la temperatura siempre
        try:
            while True:
                temp = interfaz.mostrar_temp()   # None = todavía no llegó un dato nuevo

                if temp is not None:
                    temp_actual = temp
                    print(f"Temperatura: {temp:.1f} °C", flush=True)

                # Las alertas solo se evalúan con el monitoreo activo
                if monitoreo_activo and temp_actual is not None:
                    alerta_activa = gestor.evaluar_temp(temp_actual)

                    """if alerta_activa:
                            tiempo = monitoreo.tiempo_transcurrido() or 0.0
                            base_dato.guardar_evento(
                                numero_gorra=monitoreo.numero_gorra,
                                tiempo_transcurrido=tiempo,
                                temperatura=temp_actual,
                            )"""
                else:
                    alerta_activa = False

                time.sleep(1)  # muestreo a 1 Hz

        except Exception as e:
            print(f"Error en ciclo de monitoreo: {e}")
        finally:
            lector.desconectar()
            conexion_activa = False
            temp_actual = None
        time.sleep(3)  # espera antes de reconectar


# --- Rutas de la API ---
@app.route("/")
def home():
    return render_template("index.html")


"""@app.route("/api/registrar_paciente", methods=["POST"])
def api_registrar_paciente():
    data = request.json
    interfaz.registrar_paciente(
        id_paciente=data.get("id_paciente", "S/D"),
        num_sesion=data.get("num_sesion", 0),
    )
    return jsonify({"status": "ok"})"""


@app.route("/api/registrar_gorra", methods=["POST"])
def api_registrar_gorra():
    data = request.json
    interfaz.registrar_gorra(data.get("num_gorro", 0))
    return jsonify({"status": "ok"})


@app.route("/api/configurar_umbrales", methods=["POST"])
def api_configurar_umbrales():
    global monitoreo_activo
    data = request.json
    try:
        interfaz.configurar_umbrales(
            float(data.get("temp_min", 0)),
            float(data.get("temp_max", 0)),
        )
    except (TypeError, ValueError) as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    monitoreo_activo = True
    return jsonify({"status": "ok", "message": "Monitoreo iniciado"})


@app.route("/api/silenciar", methods=["POST"])
def api_silenciar():
    global alerta_activa
    interfaz.silenciar_alerta()
    alerta_activa = False
    return jsonify({"status": "ok"})


@app.route("/api/finalizar", methods=["POST"])
def api_finalizar():
    global monitoreo_activo, alerta_activa
    monitoreo_activo = False
    alerta_activa = False
    interfaz.finalizar_sesion()
    print("⏹ MONITOREO FINALIZADO DESDE LA WEB")
    return jsonify({"status": "ok"})


@app.route("/api/obtener_estado", methods=["GET"])
def api_obtener_estado():
    return jsonify({
        "temp_actual": temp_actual,
        "alerta_activa": alerta_activa,
        "conexion": "CONECTADO" if conexion_activa else "DESCONECTADO",
        "monitoreo_activo": monitoreo_activo,
        "umbral_min": gestor.umbral_min,
        "umbral_max": gestor.umbral_max,
    })


if __name__ == "__main__":
    puerto_web = 5000
    print(f"Servidor listo en http://127.0.0.1:{puerto_web}")

    hilo = threading.Thread(target=ciclo_monitoreo, daemon=True)
    hilo.start()

    app.run(port=puerto_web, debug=False)