"""
app.py — Servidor Web y Monitoreo en Tiempo Real.
"""

import logging
import threading
import time
from clase_interfaz import Interfaz
from clase_lector import Lector
from clase_gestor_alertas import Gestor_alertas
from clase_monitoreo import Monitoreo
from flask import Flask, jsonify, render_template, request
from clase_based_datos import BaseDeDatos
from datetime import datetime

db = BaseDeDatos()

# Variables globales para ir recolectando las métricas de la sesión
datos_sesion_actual = {}
historial_temperaturas = []
contador_fuera_rango = 0
contador_silenciadas = 0
alerta_fuera_rango_previa = False # Para contar cuántas veces entró en alerta
temp_inicial_sesion = None          
esperando_temp_inicial = False   

# Variables para registrar valores únicos de temperatura que causaron alerta
temps_alerta_sesion = []
entro_al_rango_alguna_vez = False

app = Flask(__name__, template_folder=".")

# Oculta las líneas "GET /api/obtener_estado ..." para que se vea la temperatura en la terminal
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# --- Instancias reales de cada clase ---

puerto_usuario = input("Ingrese el puerto COM a utilizar (ej. COM3, COM8) [Por defecto COM3]: ").strip()
if not puerto_usuario:
    puerto_usuario = "COM3"

lector = Lector(puerto=puerto_usuario, velocidad=9600)
gestor = Gestor_alertas()
monitoreo = Monitoreo()

interfaz = Interfaz(monitoreo=monitoreo, gestor_alertas=gestor, clase_lector=lector)

# --- Estado compartido ---
monitoreo_activo = False
conexion_activa = False
alerta_activa = False
temp_actual = None 


def ciclo_monitoreo():
    """Lee el Arduino todo el tiempo. Reconecta solo si se cae."""
    global monitoreo_activo, conexion_activa, alerta_activa, temp_actual, historial_temperaturas, contador_fuera_rango, alerta_fuera_rango_previa, temp_inicial_sesion, esperando_temp_inicial, temps_alerta_sesion, entro_al_rango_alguna_vez

    while True:
        # 1) Conectar (reintenta hasta lograrlo)
        while not conexion_activa:
            conexion_activa = lector.conectar()
            if not conexion_activa:
                print("No se pudo conectar. Reintentando en 3 segundos...")
                time.sleep(3)

        # 2) Ciclo de lectura y control
        try:
            while True:
                temp = interfaz.mostrar_temp()   # <-- PRIMERO se lee, siempre

                if not monitoreo_activo:
                    alerta_activa = False
                    time.sleep(1)
                    continue

                if temp is not None:
                    temp_actual = temp
                    print(f"Temperatura: {temp:.2f} °C", flush=True)

                    # Captura de la temperatura inicial (primera lectura tras Guardar)
                    if esperando_temp_inicial:
                        temp_inicial_sesion = temp
                        esperando_temp_inicial = False

                    historial_temperaturas.append(temp_actual)

                    temp_min = datos_sesion_actual.get("temp_min", 0)
                    temp_max = datos_sesion_actual.get("temp_max", 0)

                    en_rango = (temp_min <= temp_actual <= temp_max)
                    fuera_de_rango_ahora = not en_rango

                    # Marca si ingresó al rango al menos una vez en la sesión
                    if en_rango:
                        entro_al_rango_alguna_vez = True

                    # Si ya ingresó previamente y se sale, registra valores únicos
                    if entro_al_rango_alguna_vez and fuera_de_rango_ahora:
                        if temp_actual not in temps_alerta_sesion:
                            temps_alerta_sesion.append(temp_actual)

                    if fuera_de_rango_ahora and not alerta_fuera_rango_previa:
                        contador_fuera_rango += 1

                    alerta_fuera_rango_previa = fuera_de_rango_ahora

                if temp_actual is not None:
                    try:
                        alerta_activa = gestor.evaluar_temp(temp_actual)
                    except Exception:
                        alerta_activa = False
                else:
                    alerta_activa = False

                time.sleep(1)

        except Exception as e:
            print(f"Error en ciclo de monitoreo: {e}")
        finally:
            lector.desconectar()
            conexion_activa = False
            temp_actual = None
        time.sleep(3)

# --- Rutas de la API ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/guardar", methods=["POST"])
def api_guardar():
    global monitoreo_activo, datos_sesion_actual, historial_temperaturas, contador_fuera_rango, contador_silenciadas, alerta_fuera_rango_previa, esperando_temp_inicial, temps_alerta_sesion, entro_al_rango_alguna_vez
    
    data = request.json
    try:
        id_paciente = data.get("id_paciente", "S/D")
        num_sesion = data.get("num_sesion", 0)
        num_gorro = data.get("num_gorro", 0)
        temp_min = float(data.get("temp_min", 0))
        temp_max = float(data.get("temp_max", 0))

        interfaz.registrar_paciente(id_paciente, num_sesion)
        interfaz.registrar_gorra(num_gorro)
        interfaz.configurar_umbrales(temp_min, temp_max)

        # Reiniciar contadores y guardar datos iniciales para la Base de Datos
        historial_temperaturas = []
        contador_fuera_rango = 0
        contador_silenciadas = 0
        alerta_fuera_rango_previa = False
        esperando_temp_inicial = True
        temps_alerta_sesion = []
        entro_al_rango_alguna_vez = False

        ahora = datetime.now()
        datos_sesion_actual = {
            "id_paciente": id_paciente,
            "num_sesion": num_sesion,
            "num_gorro": num_gorro,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "hora_inicio": ahora.strftime("%H:%M:%S"),
            "fecha": ahora.strftime("%Y-%m-%d")
        }

        monitoreo_activo = True
        print("▶ ¡Datos guardados! Iniciando el monitoreo térmico...")
        
        return jsonify({"status": "ok", "message": "Datos guardados y monitoreo iniciado"})
    
    except (TypeError, ValueError) as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/silenciar", methods=["POST"])
def api_silenciar():
    global alerta_activa, contador_silenciadas
    
    interfaz.silenciar_alerta()
    alerta_activa = False
    contador_silenciadas += 1  
    
    return jsonify({"status": "ok"})

@app.route("/api/finalizar", methods=["POST"])
def api_finalizar():
    global monitoreo_activo, alerta_activa, datos_sesion_actual, historial_temperaturas, contador_fuera_rango, contador_silenciadas, temp_inicial_sesion, esperando_temp_inicial, temps_alerta_sesion

    monitoreo_activo = False
    esperando_temp_inicial = False   
    alerta_activa = False

    interfaz.finalizar_sesion()

    if interfaz.monitoreo and interfaz.monitoreo.tiempo_fin:
        hora_fin = interfaz.monitoreo.tiempo_fin.strftime("%H:%M:%S")
        print(f"MONITOREO FINALIZADO DESDE LA WEB a las {hora_fin}")
    else:
        ahora = datetime.now()
        hora_fin = ahora.strftime("%H:%M:%S")
        print(f"MONITOREO FINALIZADO DESDE LA WEB a las {hora_fin}")

    # Calcular métricas térmicas de la sesión
    if historial_temperaturas:
        temp_inicial = temp_inicial_sesion if temp_inicial_sesion is not None else historial_temperaturas[0]
        temp_final = historial_temperaturas[-1]
        temp_promedio = sum(historial_temperaturas) / len(historial_temperaturas)
    else:
        temp_inicial = 0.0
        temp_final = 0.0
        temp_promedio = 0.0

    cadena_temps_alerta = ", ".join(map(str, temps_alerta_sesion)) if temps_alerta_sesion else "Ninguna"

    # Armar el diccionario completo con todas las columnas
    registro_completo = {
        'id_paciente': datos_sesion_actual.get('id_paciente', 'S/D'),
        'num_sesion': datos_sesion_actual.get('num_sesion', 0),
        'num_gorro': datos_sesion_actual.get('num_gorro', 0),
        'temp_min_umbral': datos_sesion_actual.get('temp_min', 0),
        'temp_max_umbral': datos_sesion_actual.get('temp_max', 0),
        'temp_inicial': temp_inicial,
        'temp_final': temp_final,
        'temp_promedio': round(temp_promedio, 2),
        'veces_fuera_rango': contador_fuera_rango,
        'alertas_silenciadas': contador_silenciadas,
        'temperaturas_alerta': cadena_temps_alerta,
        'hora_inicio': datos_sesion_actual.get('hora_inicio', '00:00:00'),
        'hora_fin': hora_fin,
        'fecha': datos_sesion_actual.get('fecha', datetime.now().strftime("%Y-%m-%d"))
    }

    # Guardar los datos en SQLite
    db.guardar_tratamiento(registro_completo)

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
    print(f"Servidor listo!!!!!-->-->--> en http://127.0.0.1:{puerto_web}")

    hilo = threading.Thread(target=ciclo_monitoreo, daemon=True)
    hilo.start()

    app.run(port=puerto_web, debug=False)