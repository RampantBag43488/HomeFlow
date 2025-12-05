# HomeFlow
### Joel García Guzmán
### Manuel Valentino Ortiz Sánchez
### Hector Alejandro Barron Tamayo
### Iñaki Mancera Llan
Nuestro proyecto es una solución de monitoreo de hogares, principalmente en el aspecto de entrada y salida de personas. Es un sistema el cual con láseres posicionados correctamente puede detectar cuántas personas salen y entran a tu hogar. Esto también detecta los momentos en que la puerta se abre, cuantas personas hay en casa y envía notificaciones para cuando alguien entra y sale.

## DataBase en SQL
EL contenido de esta seccion en el repositorio es el codigo base para sql que crea las tablas necesarias y sus columnas para que luego sea insertada la informacion en tiempor eal que recible el dispositovo.

## server2.py
Servidor backend desarrollado con Flask que recibe los datos enviados desde el ESP32 (estado de puerta y detección de movimiento), los procesa y los almacena en una base de datos MySQL.
Incluye inicialización automática de Usuario, Cuarto, Dispositivo y sensores base, además de un endpoint para registrar eventos en tiempo real.

## Proyecto_iot.ino
Código del ESP32 que gestiona los sensores del proyecto IoT: el sensor magnético de puerta y dos sensores ultrasónicos para detectar entrada y salida de personas.
Envía los datos mediante una petición HTTP POST al servidor Flask (server2.py).
Implementa lógica de lectura y clasificación de movimiento (entrada/salida).
