from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime 
import random

db_config = {
    "host": "localhost",      
    "user": "root",           
    "password": "",           
    "database": "proyecto" 
}

def get_connection():
    return mysql.connector.connect(**db_config)

def generar_id():
    """ID aleatorio de enteros (7 dígitos)."""
    return random.randint(1_000_000, 9_999_999)

USER_ID = None
CUARTO_ID = None
DISPOSITIVO_ID = None

def init_usuario_cuarto_dispositivo():
    """
    Crea una fila en Usuario, Cuarto y Dispositivo
    SOLO si aún no existen.
    Guarda sus IDs en variables globales.
    """
    global USER_ID, CUARTO_ID, DISPOSITIVO_ID

    conn = get_connection()
    cursor = conn.cursor()

    # 1) Usuario (tomando user y password de db_config)
    cursor.execute("SELECT UserID FROM Usuario LIMIT 1")
    row = cursor.fetchone()
    if row:
        USER_ID = int(row[0])
    else:
        USER_ID = generar_id()
        nombre = db_config["user"]
        contrasena = db_config["password"]
        cursor.execute(
            "INSERT INTO Usuario (UserID, Nombre, Contrasena) VALUES (%s, %s, %s)",
            (USER_ID, nombre, contrasena)
        )

    # 2) Cuarto
    cursor.execute("SELECT CuartoID FROM Cuarto LIMIT 1")
    row = cursor.fetchone()
    if row:
        CUARTO_ID = int(row[0])
    else:
        CUARTO_ID = generar_id()
        cursor.execute(
            "INSERT INTO Cuarto (CuartoID, UserID, Nombre) VALUES (%s, %s, %s)",
            (CUARTO_ID, USER_ID, "Casa")
        )

    # 3) Dispositivo
    cursor.execute("SELECT DispositivoID FROM Dispositivo LIMIT 1")
    row = cursor.fetchone()
    if row:
        DISPOSITIVO_ID = int(row[0])
    else:
        DISPOSITIVO_ID = generar_id()
        # Estado = 1 si corrió bien
        cursor.execute(
            "INSERT INTO Dispositivo (DispositivoID, CuartoID, Estado) VALUES (%s, %s, %s)",
            (DISPOSITIVO_ID, CUARTO_ID, 1)
        )

    conn.commit()
    cursor.close()
    conn.close()

def init_sensores_basicos():
    """
    Crea tres sensores fijos si no existen:
      - magnético puerta (GPIO23)
      - ultrasonico dentro  (echo GPIO19)
      - ultrasonico fuera   (echo GPIO18)
    Solo se crean si no están ya en la tabla Sensor.
    """
    conn = get_connection()
    cursor = conn.cursor()

    sensores_def = [
        ("magnetico",          "GPIO23"),
        ("ultrasonico_dentro", "GPIO19"),
        ("ultrasonico_fuera",  "GPIO18"),
    ]

    for tipo, pin in sensores_def:
        cursor.execute(
            "SELECT SensorID FROM Sensor WHERE Tipo = %s AND Pin = %s LIMIT 1",
            (tipo, pin)
        )
        row = cursor.fetchone()
        if not row:
            sensor_id = generar_id()
            cursor.execute(
                "INSERT INTO Sensor (SensorID, DispositivoID, Tipo, Pin) VALUES (%s, %s, %s, %s)",
                (sensor_id, DISPOSITIVO_ID, tipo, pin)
            )

    conn.commit()
    cursor.close()
    conn.close()


def save_to_db(estado_puerta_int, movimiento):
    """
    Guarda un evento en la tabla Evento.
    - EventoID, CuartoID, EventoES, EventoAC son INT
    - SensorID se inserta como NULL
    - Fecha es DATETIME.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Si no hay ni puerta ni movimiento, no tiene caso guardar
    if estado_puerta_int is None and movimiento is None:
        cursor.close()
        conn.close()
        return

    fechaActual = datetime.now()

    # ID aleatorio para el evento
    eventID = generar_id()

    # --- Mapear movimiento (string) a entero (EventoES) ---
    if movimiento is None:
        evento_es = 0          # sin movimiento
    else:
        mov_norm = movimiento.strip().lower()
        if mov_norm == "entrada":
            evento_es = 1
        elif mov_norm == "salida":
            evento_es = 2
        else:
            evento_es = -1     # desconocido

    # --- Mapear estado de puerta a entero (EventoAC) ---
    if estado_puerta_int is None:
        evento_ac = -1         # sin dato
    else:
        if estado_puerta_int == 1:
            evento_ac = 1      # abierta
        elif estado_puerta_int == 0:
            evento_ac = 0      # cerrada
        else:
            evento_ac = -1     # desconocido

    # SensorID se guarda como NULL
    sensor_id = None

    query = """
        INSERT INTO Evento (EventoID, CuartoID, SensorID, EventoES, EventoAC, Fecha)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (eventID, CUARTO_ID, sensor_id, evento_es, evento_ac, fechaActual)

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()


# Inicializa la aplicación Flask
app = Flask(__name__)

HOST_IP = '0.0.0.0' 
PORT_NUMBER = 5000 

@app.before_request
def startup():
    """
    Se ejecuta una sola vez cuando llega la primera petición al servidor.
    Inicializa Usuario, Cuarto, Dispositivo y los 3 sensores base.
    """
    init_usuario_cuarto_dispositivo()
    init_sensores_basicos()
    print("✔ Usuario, Cuarto, Dispositivo y Sensores básicos inicializados.")


@app.route('/data', methods=['POST'])
def receive_data():
    print("--- Petición POST recibida ---")

    estado_puerta = request.form.get('estado_puerta')
    movimiento = request.form.get('movimiento')

    if estado_puerta is None and movimiento is None:
        print("ERROR: No se encontró ni 'estado_puerta' ni 'movimiento'.")
        print("Datos recibidos:", request.form)
        return jsonify({"message": "Error: Variables desconocidas"}), 400

    estado_int = None
    mov_norm = None

    # --------- PUERTA ----------
    if estado_puerta is not None:
        try:
            estado_int = int(estado_puerta)
        except ValueError:
            print(f"Valor recibido invalido: {estado_puerta}")
            return jsonify({"message": "Valor del sensor invalido"}), 400

        if estado_int == 1:
            print("✅ Puerta: ABIERTA")
        elif estado_int == 0:
            print("🚪 Puerta: CERRADA")
        else:
            print(f"⚠ Estado de puerta desconocido: {estado_int}")

    # --------- MOVIMIENTO ----------
    if movimiento is not None:
        mov_norm = movimiento.strip().lower()
        print(f"🚶 DETECCIÓN DE PERSONA: {mov_norm.upper()}")

        if mov_norm == "entrada":
            print("   -> Alguien ha entrado a la casa")
        elif mov_norm == "salida":
            print("   <- Alguien ha salido de la casa")

    # --------- GUARDAR EN BD ----------
    try:
        save_to_db(estado_puerta_int=estado_int, movimiento=mov_norm)
    except Exception as e:
        print("ERROR guardando en BD:", e)
        return jsonify({"message": "Error guardando en BD"}), 500

    return jsonify({"message": "Datos recibidos correctamente"}), 200


if __name__ == '__main__':
    print(f"Iniciando servidor Flask en http://{HOST_IP}:{PORT_NUMBER}")
    app.run(host=HOST_IP, port=PORT_NUMBER, debug=True, threaded=True)