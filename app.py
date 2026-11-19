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
import matplotlib
matplotlib.use('Agg')  # Para generar gráficos en segundo plano sin abrir ventanas GUI
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

db = BaseDeDatos()

# Variables globales para ir recolectando las métricas de la sesión
datos_sesion_actual = {}
historial_temperaturas = []
contador_fuera_rango = 0
contador_silenciadas = 0
alerta_fuera_rango_previa = False # Para contar cuántas veces entró en alerta
temp_inicial_sesion = None          
esperando_temp_inicial = False   

# Variables para registrar valores únicos de que causaron alerta
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

                    # 1. Si la temperatura está (o entra) en rango por primera vez, activamos la bandera
                    if en_rango:
                        entro_al_rango_alguna_vez = True

                    # 2. SOLO si ya tocó el rango en algún momento de la sesión y AHORA se sale,
                    # se registran las temperaturas de alerta de ahí en adelante (sin duplicar)
                    if entro_al_rango_alguna_vez and fuera_de_rango_ahora:
                        if temp_actual not in temps_alerta_sesion:
                            temps_alerta_sesion.append(temp_actual)

                    # 3. Contador de eventos/transiciones de salida de rango
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
        temps_alerta_sesion = []           # 👈 Reinicio limpio de alertas
        entro_al_rango_alguna_vez = False  # 👈 Reinicio de bandera de 1ª vez

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
        'temperatura_alerta': cadena_temps_alerta,
        'hora_inicio': datos_sesion_actual.get('hora_inicio', '00:00:00'),
        'hora_fin': hora_fin,
        'fecha': datos_sesion_actual.get('fecha', datetime.now().strftime("%Y-%m-%d"))
    }

    # Guardar los datos en SQLite
    db.guardar_tratamiento(registro_completo)

    # Generar el gráfico automáticamente al finalizar
    id_paciente = datos_sesion_actual.get('id_paciente', 'SD')
    num_sesion = datos_sesion_actual.get('num_sesion', 0)
    temp_min = datos_sesion_actual.get('temp_min', 0)
    temp_max = datos_sesion_actual.get('temp_max', 0)

    # Generar imagen para el póster
    nombre_grafico = generar_grafico_sesion(
        historial_temps=historial_temperaturas,
        temp_min=temp_min,
        temp_max=temp_max,
        temps_alerta=temps_alerta_sesion,
        num_sesion=num_sesion,
        id_paciente=id_paciente
    )

    # ... (guardado en la base de datos con db.guardar_tratamiento(registro_completo)) ...

    monitoreo_activo = False
    return jsonify({"status": "ok", "grafico": nombre_grafico})

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

def generar_grafico_sesion(historial_temps, temp_min, temp_max, temps_alerta, num_sesion, id_paciente):
    """
    Genera y guarda el gráfico de temperatura vs tiempo para el póster académico.
    """
    if not historial_temps:
        print("No hay datos de temperatura para graficar.")
        return None

    # Eje X: Convertir lecturas por segundo a minutos (0, 1/60, 2/60...)
    tiempo_minutos = [i / 60.0 for i in range(len(historial_temps))]

    # Crear la figura y los ejes
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)

    # 1. Banda horizontal sombreada para el rango terapéutico configurado
    ax.axhspan(temp_min, temp_max, color='#2ECC71', alpha=0.18, label=f'Rango Terapéutico ({temp_min}°C - {temp_max}°C)')

    # Lineas punteadas para delimitar visualmente los umbrales
    ax.axhline(temp_min, color='#27AE60', linestyle='--', linewidth=1.2)
    ax.axhline(temp_max, color='#27AE60', linestyle='--', linewidth=1.2)

    # 2. Curva principal de temperatura (línea suave con puntos negros por segundo)
    ax.plot(tiempo_minutos, historial_temps, color='#2C3E50', linewidth=1.5, zorder=2)
    ax.scatter(tiempo_minutos, historial_temps, color='black', s=12, label='Lectura por segundo', zorder=3)

    # 3. Marcar con puntos rojos bien definidos las temperaturas de alerta guardadas en la BD
    alertas_x = []
    alertas_y = []
    
    # Identificar las posiciones de las temperaturas en la lista de alertas
    for t_min, temp in zip(tiempo_minutos, historial_temps):
        if temp in temps_alerta:
            alertas_x.append(t_min)
            alertas_y.append(temp)

    if alertas_x:
        ax.scatter(alertas_x, alertas_y, color='#E74C3C', edgecolor='black', s=50, linewidth=0.8, label='Temperatura de Alerta', zorder=4)

    # 4. Configuración de ejes y escalas
    ax.set_ylim(0, 50)  # Eje vertical de 0 a 50°C
    
    # 👈 CORREGIDO AQUÍ: Genera marcas desde 0 hasta 50 cada 2.5°C (0, 2.5, 5.0 ... 47.5, 50.0)
    ax.set_yticks(np.arange(0, 51, 2.5)) 
    
    # Ajuste automático del eje horizontal en minutos
    max_minutos = max(tiempo_minutos) if tiempo_minutos else 1
    ax.set_xlim(0, max_minutos * 1.05)

    # Estilizado para el póster académico
    ax.set_title(f"Registro Térmico de la Sesión N° {num_sesion} - Paciente: {id_paciente}", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Tiempo (minutos)", fontsize=11, labelpad=8)
    ax.set_ylabel("Temperatura (°C)", fontsize=11, labelpad=8)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', framealpha=0.9, fontsize=9)

    plt.tight_layout()

    # Guardar imagen PNG con alta resolución para el póster
    nombre_archivo = f"grafico_sesion_{num_sesion}_{id_paciente}.png"
    plt.savefig(nombre_archivo, format='png', dpi=300)
    plt.close()
    
    print(f"Grafico generado con éxito: {nombre_archivo}")
    return nombre_archivo

if __name__ == "__main__":
    puerto_web = 5000
    print(f"Servidor listo!!!!!-->-->--> en http://127.0.0.1:{puerto_web}")

    hilo = threading.Thread(target=ciclo_monitoreo, daemon=True)
    hilo.start()

    app.run(port=puerto_web, debug=False)