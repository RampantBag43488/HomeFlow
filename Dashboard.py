import streamlit as st
import pandas as pd
import plotly.express as px
import time
import random
from datetime import datetime
import base64
import os

# CONFIGURACION INICIAL
st.set_page_config(
    page_title="Dashboard Seguridad",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# FUNCIONES AUXILIARES (NUEVO: PARA LAS IMAGENES)
def img_to_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode('utf-8').replace('\n', '')
    except Exception as e:
        return None

# CONFIGURACION DE BASE DE DATOS (XAMPP)
USAR_DB_REAL = True

# Credenciales de XAMPP
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',      # Usuario por defecto de XAMPP
    'password': '',      # XAMPP no tiene contraseña inicialmente
    'database': 'proyecto' # Nombre de base de datos
}

# FUNCIONES DE BASE DE DATOS
def obtener_conexion():
    """Crea la conexión a MySQL usando las credenciales de arriba."""
    import mysql.connector
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        st.error(f"Error conectando a MySQL: {e}")
        return None

def obtener_datos_reales():
    """
    Consulta la base de datos real con la lógica corregida:
    - EventoES: 1 (Entra), 2 (Sale), 0 (Nada)
    - EventoAC: 1 (Abierta), 0 (Cerrada), -1 (Sin cambio)
    """
    conn = obtener_conexion()
    if not conn:
        return None, None, None, None, pd.DataFrame()

    cursor = conn.cursor(dictionary=True)
  
    # ESTADO DE LA PUERTA
    # Se busca el ultimo registro donde la puerta SI dijo algo (0 o 1).
    # Se ignora el -1 porque significa "no hubo cambio en la puerta".
    query_puerta = """
        SELECT EventoAC 
        FROM Evento 
        WHERE EventoAC IN (0, 1) 
        ORDER BY Fecha DESC 
        LIMIT 1
    """
    cursor.execute(query_puerta)
    result_puerta = cursor.fetchone()
    
    # Si no hay datos, asumimos cerrada (0), si hay, se toma el valor.
    estado_puerta = result_puerta['EventoAC'] if result_puerta else 0 

    # CONTEO DE PERSONAS
    # Se cuenta cuantas veces aparece el 1 (Entradas)
    query_entradas = "SELECT COUNT(*) as total FROM Evento WHERE EventoES = 1"
    cursor.execute(query_entradas)
    entradas = cursor.fetchone()['total']

    # Se cuenta cuantas veces aparece el 2 (Salidas)
    query_salidas = "SELECT COUNT(*) as total FROM Evento WHERE EventoES = 2"
    cursor.execute(query_salidas)
    salidas = cursor.fetchone()['total']
    
    # Se calculan las personas dentro
    ocupacion = entradas - salidas
    if ocupacion < 0: ocupacion = 0 

    # ESTADO DEL SISTEMA (Dispositivo)
    # Se verifica si el dispositivo esta en estado 1
    query_sis = "SELECT Estado FROM Dispositivo ORDER BY DispositivoID DESC LIMIT 1"
    cursor.execute(query_sis)
    res_sis = cursor.fetchone()
    sistema_ok = res_sis['Estado'] if res_sis else 0

    # ULTIMA ACTIVIDAD (CAMBIO SOLICITADO)
    # Se busca la fecha más reciente donde hubo Entrada(1), Salida(2)
    # O donde la puerta se Abrio(1) o Cerro(0).
    query_last = """
        SELECT Fecha FROM Evento 
        WHERE EventoES IN (1, 2) OR EventoAC IN (0, 1) 
        ORDER BY Fecha DESC 
        LIMIT 1
    """
    cursor.execute(query_last)
    res_last = cursor.fetchone()
    ultima_entrada = res_last['Fecha'].strftime("%H:%M:%S") if res_last else "--:--"

    # DATOS PARA LA GRÁFICA
    # Se trae solo Entradas (1) y Salidas (2) para la línea de tiempo.
    # Se ignora 0 (nada)
    query_hist = """
        SELECT Fecha, EventoES 
        FROM Evento 
        WHERE EventoES IN (1, 2) 
        ORDER BY Fecha ASC
    """
    cursor.execute(query_hist)
    datos_hist = cursor.fetchall()
    df = pd.DataFrame(datos_hist)
    
    conn.close()
    
    return estado_puerta, ocupacion, sistema_ok, ultima_entrada, df

# INTERFAZ GRAFICA (DASHBOARD)
st.title("Control de accesos")

# Contenedor principal que se actualizara constantemente
placeholder = st.empty()

while True:
    # OBTENER DATOS (Switch entre Real o Simulado)
    if USAR_DB_REAL:
        try:
            p_estado, num_personas, sys_ok, last_entry, df_hist = obtener_datos_reales()
        except Exception as e:
            st.error(f"Error en la consulta SQL (revisa tus tablas): {e}")
            break

    # Si hubo error de conexion y devolvio None
    if df_hist is None:
        time.sleep(5)
        continue

    # RENDERIZAR LA PANTALLA
    with placeholder.container():
        
        # PRIMERA FILA (3 COLUMNAS)
        c1, c2, c3 = st.columns(3)

# CUADRO 1: ESTADO PUERTA
        with c1:
            if p_estado == 0:
                bg_color = "#28a745" # Verde
                txt_estado = "Puerta cerrada"
                archivo_img = "puertaCerrada.png"
            else:
                bg_color = "#dc3545" # Rojo
                txt_estado = "PUERTA ABIERTA"
                archivo_img = "puertaAbierta.png"

            # Se convierte la imagen
            img_b64 = img_to_base64(archivo_img)
            
            # Se prepara la etiqueta de la imagen
            if img_b64:
                tag_imagen = f'<img src="data:image/png;base64,{img_b64}" width="80" style="display:block; margin: 0 auto 10px auto;">'
            else:
                tag_imagen = '<div style="font-size: 50px;">🚪</div>'

            # Se pega todo el HTML a la izquierda del todo en la variable
            html_content = f"""
<div style="background-color: {bg_color}; padding: 20px; border-radius: 10px; color: white; text-align: center; height: 180px; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<div style="font-size: 25px; font-weight: bold;">{txt_estado}</div>
{tag_imagen}
</div>
"""
            # Se envia la variable
            st.markdown(html_content, unsafe_allow_html=True)


# CUADRO 2: CONTADOR (CON IMAGEN)
        with c2:
            # Se convierte la imagen
            img_head_b64 = img_to_base64("head.png")
            
            # Se crea la etiqueta de imagen o usar emoji de respaldo
            if img_head_b64:
                # 'vertical-align: middle' alinea la imagen con el centro del numero
                # 'margin-left: 15px' le da un espacio para que no este pegada al numero
                head_icon = f'<img src="data:image/png;base64,{img_head_b64}" width="50" style="vertical-align: middle; margin-left: 15px;">'
            else:
                head_icon = "👤"

            # flex en el div del numero para que la imagen y el texto se alineen perfecto
            html_c2 = f"""
<div style="background-color: #f8f9fa; border: 2px solid #e9ecef; padding: 15px; border-radius: 10px; text-align: center; height: 180px; flex-direction: column; justify-content: center; align-items: center;">
<div style="font-size: 25px; margin-bottom: 5px; ">Personas en casa</div>
<div style="font-size: 50px; font-weight: bold; align-items: center; justify-content: center;">
{num_personas}
{head_icon}
</div>
</div>
"""
            st.markdown(html_c2, unsafe_allow_html=True)

        # CUADRO 3: INFO SISTEMA
        with c3:
            lbl_sys = "Activo" if sys_ok == 1 else "Error!"
            color_sys = "green" if sys_ok == 1 else "red"
            
            st.markdown(f"""
            <div style="
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                padding: 20px;
                border-radius: 10px;
                height: 180px;
                display: flex; 
                flex-direction: column; 
                justify-content: center;">
                <div style="font-size: 25px; margin-bottom:10px;">
                    Estado Sistema: <b style="color: {color_sys};">{lbl_sys}</b>
                </div>
                <div style="font-size: 25px;">
                    Último movimiento:
                    <span style="font-size: 25px; font-weight: bold;">{last_entry}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# SEGUNDA FILA (GRÁFICA ESCALONADA + MARCADORES + TIEMPO REAL)
        st.write("---")
        
        if not df_hist.empty:
            # Se preparan los datos historicos
            df_chart = df_hist.copy()
            df_chart['Cambio'] = df_chart['EventoES'].apply(lambda x: 1 if x == 1 else -1)
            df_chart['Ocupacion_Historica'] = df_chart['Cambio'].cumsum()
            
            # Se ajusta para evitar negativos en los datos
            minimo = df_chart['Ocupacion_Historica'].min()
            if minimo < 0:
                df_chart['Ocupacion_Historica'] += abs(minimo)

            # Se obtiene la ultima ocupacion registrada
            ultima_ocupacion = df_chart['Ocupacion_Historica'].iloc[-1]
            
            # Se crea una fila "falsa" con la hora actual y la misma ocupacion
            fila_ahora = pd.DataFrame({
                'Fecha': [datetime.now()],
                'EventoES': [0],  # Se pone 0 para que NO salga ni punto verde ni X roja
                'Ocupacion_Historica': [ultima_ocupacion]
            })
            
            # Se pega esta fila al final de los datos para la grafica
            # (Se usa concat porque append esta obsoleto en pandas nuevos)
            df_chart = pd.concat([df_chart, fila_ahora], ignore_index=True)
            # ------------------------------------------------

            # BASE: Grafica de area ESCALONADA ('hv')
            fig = px.area(
                df_chart, 
                x='Fecha', 
                y='Ocupacion_Historica',
                title="<b>Registro de Actividad en Tiempo Real</b>",
                color_discrete_sequence=['rgba(0, 123, 255, 0.2)'], 
                height=350,
                line_shape='hv' # Mantiene la forma de escalera
            )
            
            # MARCADORES (Solo para eventos reales 1 y 2, ignorando el 0 de "ahora")
            entradas = df_chart[df_chart['EventoES'] == 1]
            salidas = df_chart[df_chart['EventoES'] == 2]

            # Puntos Verdes (ENTRADAS)
            fig.add_scatter(
                x=entradas['Fecha'], 
                y=entradas['Ocupacion_Historica'],
                mode='markers',
                name='Entrada',
                marker=dict(color='#28a745', size=12, symbol='circle', line=dict(width=2, color='white'))
            )

            # Cruces Rojas (SALIDAS)
            fig.add_scatter(
                x=salidas['Fecha'], 
                y=salidas['Ocupacion_Historica'],
                mode='markers',
                name='Salida',
                marker=dict(color='#dc3545', size=12, symbol='x', line=dict(width=2, color='white'))
            )

            # Ajustes Visuales
            fig.update_layout(
                xaxis_title=None,
                yaxis_title="Personas",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hovermode="x unified",
                # Aseguramos que el eje X muestre hasta el momento actual
                xaxis_range=[df_chart['Fecha'].min(), datetime.now()] 
            )
            
            # Linea visible
            fig.update_traces(selector=dict(type='area'), line=dict(color='#007bff', width=3))

            st.plotly_chart(fig, use_container_width=True, key=f"grafica_{time.time()}")
            
        else:
            st.info("Esperando eventos para graficar...")

    # Pausa para no saturar el procesador (Simula actualizacion cada 2 seg)
    time.sleep(2)
