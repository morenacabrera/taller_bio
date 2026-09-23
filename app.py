"""
app.py — Servidor Web y Monitoreo en Tiempo Real
"""

import threading
import time
from clase_interfaz import Interfaz
from clase_lector import Lector
from flask import Flask, jsonify, render_template, request

# TODO: Descomentar cuando existan las clases restantes
# from gestor_alertas import Gestor_alertas
# from base_dato import Base_dato
# from monitoreo import Monitoreo

app = Flask(__name__, template_folder=".")

# --- Configuración de Puerto ---
PUERTO = "COM3"
VELOCIDAD = 9600

# --- Instancias e Indicadores del Sistema ---
lector = Lector(puerto=PUERTO, velocidad=VELOCIDAD)
gestor = None
base_dato = None
monitoreo = None

interfaz = Interfaz(
    monitoreo=monitoreo, gestor_alertas=gestor, base_dato=base_dato
)

# Variable global para controlar cuándo inicia el monitoreo desde la web
monitoreo_activo = False


def ciclo_monitoreo():
    """Ejecuta la lectura del Arduino en segundo plano solo si fue activado desde la web"""
    global monitoreo_activo

    if lector.conectar():
        interfaz.actualizar_estado_conexion(True)
        try:
            while True:
                # Si el usuario no presionó "Guardar" en la web, el bucle espera
                if not monitoreo_activo:
                    time.sleep(0.5)
                    continue

                temp = lector.leer_temperatura()
                if temp is not None:
                    interfaz.mostrar_temp(temp)

                    # Evaluación de umbrales si la temperatura sale del rango configurado
                    if interfaz.temp_min > 0 or interfaz.temp_max > 0:
                        if temp < interfaz.temp_min:
                            print(
                                f" ⚠️ [ALERTA] Temperatura ({temp:.1f} °C) por DEBAJO del mínimo ({interfaz.temp_min} °C)!"
                            )
                        elif temp > interfaz.temp_max:
                            print(
                                f" ⚠️ [ALERTA] Temperatura ({temp:.1f} °C) por ENCIMA del máximo ({interfaz.temp_max} °C)!"
                            )

                    if gestor is not None:
                        gestor.evaluar_temp(temp)

                time.sleep(1)  # Muestreo a 1 Hz
        except Exception as e:
            print(f"Error en ciclo de monitoreo: {e}")
        finally:
            lector.desconectar()
            interfaz.actualizar_estado_conexion(False)
    else:
        interfaz.actualizar_estado_conexion(False)


# --- Rutas de la API ---
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/configurar_umbrales", methods=["POST"])
@app.route("/api/registrar_paciente", methods=["POST"])
def api_iniciar_sesion():
    global monitoreo_activo
    data = request.json

    # Lectura de los valores ingresados en el formulario web
    id_paciente = data.get("id_paciente", "S/D")
    num_sesion = data.get("num_sesion", 0)
    num_gorro = data.get("num_gorro", 0)
    temp_min = float(data.get("temp_min", 0))
    temp_max = float(data.get("temp_max", 0))

    print("\n" + "=" * 60)
    print(" 📋 CONFIGURACIÓN RECIBIDA DESDE LA WEB:")
    interfaz.registrar_paciente(id_paciente, num_sesion)
    interfaz.registrar_gorra(num_gorro)
    interfaz.configurar_umbrales(temp_min, temp_max)
    print(" 🚀 INICIANDO MONITOREO Y EVALUACIÓN DE RANGOS...")
    print("=" * 60 + "\n")

    # Activa la lectura y evaluación de temperatura en el hilo secundario
    monitoreo_activo = True
    return jsonify({"status": "ok", "message": "Monitoreo iniciado"})


@app.route("/api/silenciar", methods=["POST"])
def api_silenciar():
    interfaz.silenciar_alerta()
    return jsonify({"status": "ok"})


@app.route("/api/finalizar", methods=["POST"])
def api_finalizar():
    global monitoreo_activo
    monitoreo_activo = False
    interfaz.finalizar_tratamiento()
    print(" ⏹ MONITOREO FINALIZADO DESDE LA WEB")
    return jsonify({"status": "ok"})


@app.route("/api/obtener_estado", methods=["GET"])
def api_obtener_estado():
    alerta = False
    if monitoreo_activo and (interfaz.temp_min > 0 or interfaz.temp_max > 0):
        if (
            interfaz.temp_actual < interfaz.temp_min
            or interfaz.temp_actual > interfaz.temp_max
        ):
            alerta = True

    return jsonify(
        {
            "temp_actual": interfaz.temp_actual if monitoreo_activo else 0.0,
            "alerta_activa": alerta,
            "conexion": interfaz.estado_conexion,
            "monitoreo_activo": monitoreo_activo,
        }
    )


if __name__ == "__main__":
    puerto_web = 5000
    url = f"http://127.0.0.1:{puerto_web}"

    print("\n" + "=" * 60)
    print(" 🌐 SERVIDOR LISTO. ABRÍ EL SIGUIENTE ENLACE EN TU NAVEGADOR:")
    print(f"    👉 {url}")
    print(
        " ⏳ Esperando que completes la interfaz web y guardes los rangos..."
    )
    print("=" * 60 + "\n")

    # Arrancar el monitoreo en segundo plano (en espera de activación)
    hilo = threading.Thread(target=ciclo_monitoreo, daemon=True)
    hilo.start()

    app.run(port=puerto_web, debug=False)