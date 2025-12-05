# HomeFlow
### Joel García Guzmán
### Manuel Valentino Ortiz Sánchez
### Hector Alejandro Barron Tamayo
### Iñaki Mancera Llan
Nuestro proyecto es una solucion de monitoreo de hogares, principalmente en el aspecto de entrada y salida de personas. Es un sistema el cual con sensores ultrasonicos posicionados correctamente puede detectar cuantas personas salen y entran a tu hogar. Esto tambien detecta los momentos en que la puerta se abre, cuantas personas hay en casa y envia notificaciones para cuando alguien entra y sale.

## DataBase en SQL
Desarrollado con MySQL.
El contenido de esta seccion en el repositorio es el codigo base para sql que crea las tablas necesarias y sus columnas para que luego sea insertada la informacion en tiempor eal que recible el dispositovo.

## server2.py
Servidor backend desarrollado con Flask que recibe los datos enviados desde el ESP32 (estado de puerta y deteccion de movimiento), los procesa y los almacena en una base de datos MySQL.
Incluye inicializacion automatica de Usuario, Cuarto, Dispositivo y sensores base, ademas de un endpoint para registrar eventos en tiempo real.

## Proyecto_iot.ino
Codigo del ESP32 que gestiona los sensores del proyecto IoT: el sensor magnetico de puerta y dos sensores ultrasonicos para detectar entrada y salida de personas.
Envía los datos mediante una petición HTTP POST al servidor Flask (server2.py).
Implementa logica de lectura y clasificacion de movimiento (entrada/salida).

## Dashboard.py
Aplicacion desarrollada con Streamlit, MySQL y Plotly que muestra en tiempo real el estado de la puerta, el numero de personas dentro de la casa y el estado del sistema de seguridad. El dashboard se conecta a la base de datos proyecto y lee la tabla Evento para calcular entradas, salidas y ocupacion. Incluye tarjetas visuales (puerta abierta/cerrada, contador de personas, estado del dispositivo) y una grafica escalonada de la actividad historica de accesos, actualizada automaticamente cada pocos segundos.
