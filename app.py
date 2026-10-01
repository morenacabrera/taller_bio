"""
app.py — Servidor Web y Monitoreo en Tiempo Real.
"""

import logging
import threading
import time
from clase_interfaz import Interfaz
from clase_lector import Lector
from clase_gestor_alertas import Gestor_alertas
from Clase_monitoreo import Monitoreo
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

app = Flask(__name__, template_folder=".")

# Oculta las líneas "GET /api/obtener_estado ..." para que se vea la temperatura en la terminal
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# --- Configuración de puerto ---
PUERTO = "COM3"
VELOCIDAD = 9600

# --- Instancias reales de cada clase ---
lector = Lector(puerto=PUERTO, velocidad=VELOCIDAD)
gestor = Gestor_alertas()
monitoreo = Monitoreo()

interfaz = Interfaz(monitoreo=monitoreo, gestor_alertas=gestor, clase_lector=lector)

# --- Estado compartido ---
monitoreo_activo = False
conexion_activa = False
alerta_activa = False
temp_actual = None          # última temperatura leída (siempre se actualiza)

def ciclo_monitoreo():
    """Lee el Arduino todo el tiempo. Reconecta solo si se cae."""
    global monitoreo_activo, conexion_activa, alerta_activa, temp_actual, historial_temperaturas, contador_fuera_rango, alerta_fuera_rango_previa

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
                temp = interfaz.mostrar_temp()   # Lee el dato del puerto serie

                # 🛑 SI EL MONITOREO NO ESTÁ ACTIVO (Aún no se presionó "Guardar"):
                if not monitoreo_activo:
                    alerta_activa = False
                    time.sleep(1)
                    continue  # Salta a la siguiente vuelta sin procesar

                # ✅ SI EL MONITOREO ESTÁ ACTIVO:
                if temp is not None:
                    temp_actual = temp
                    print(f"Temperatura: {temp:.1f} °C", flush=True)

                    # --- REGISTRO PARA LA BASE DE DATOS ---
                    historial_temperaturas.append(temp_actual)
                    
                    # Comprobar si está fuera de rango para sumar al contador
                    temp_min = datos_sesion_actual.get("temp_min", 0)
                    temp_max = datos_sesion_actual.get("temp_max", 0)
                    
                    fuera_de_rango_ahora = (temp_actual < temp_min or temp_actual > temp_max)
                    
                    # Si antes estaba bien y ahora está fuera de rango, sumamos 1 vez que se salió
                    if fuera_de_rango_ahora and not alerta_fuera_rango_previa:
                        contador_fuera_rango += 1
                        
                    alerta_fuera_rango_previa = fuera_de_rango_ahora

                # Evaluar alertas de forma segura
                if temp_actual is not None:
                    try:
                        alerta_activa = gestor.evaluar_temp(temp_actual)
                    except Exception:
                        alerta_activa = False
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

@app.route("/api/guardar", methods=["POST"])
def api_guardar():
    """
    Ruta unificada: Al presionar 'Guardar' en la interfaz web, 
    registra el paciente, la gorra, configura los umbrales y arranca el monitoreo.
    """
    global monitoreo_activo, datos_sesion_actual, historial_temperaturas, contador_fuera_rango, contador_silenciadas, alerta_fuera_rango_previa
    
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
    global monitoreo_activo, alerta_activa, datos_sesion_actual, historial_temperaturas, contador_fuera_rango, contador_silenciadas
    
    monitoreo_activo = False
    alerta_activa = False
    
    interfaz.finalizar_sesion()
    
    if interfaz.monitoreo and interfaz.monitoreo.tiempo_fin:
        hora_fin = interfaz.monitoreo.tiempo_fin.strftime("%H:%M:%S")
        print(f"⏹ MONITOREO FINALIZADO DESDE LA WEB a las {hora_fin}")
    else:
        ahora = datetime.now()
        hora_fin = ahora.strftime("%H:%M:%S")
        print(f"⏹ MONITOREO FINALIZADO DESDE LA WEB a las {hora_fin}")
        
    # Calcular métricas térmicas de la sesión
    if historial_temperaturas:
        temp_inicial = historial_temperaturas[0]
        temp_final = historial_temperaturas[-1]
        temp_promedio = sum(historial_temperaturas) / len(historial_temperaturas)
    else:
        temp_inicial = 0.0
        temp_final = 0.0
        temp_promedio = 0.0

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