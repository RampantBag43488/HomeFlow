#include <WiFi.h>
#include <HTTPClient.h>

// Configuracion del servidor
const char* serverName = "http://10.197.192.219:5000/data"; 

// --- PINES ---
const int SENSOR_PIN_PUERTA = 23; 
const int ECHO_DENTRO = 13;
const int TRIG_DENTRO = 12;
const int ECHO_FUERA = 18;
const int TRIG_FUERA = 16;

// --- VARIABLES DE DISTANCIA ---
long dActualDentro = 0;   
long dActualFuera = 0;

// --- CONFIGURACIÓN DE CONTEO ---
const int DISTANCIA_MAXIMA = 15; // Si mide menos de 80cm, hay una persona
int secuencia = 0; // 0: Nadie, 1: Detectó fuera primero (Entrando), 2: Detectó dentro primero (Saliendo)
bool sensorFueraActivo = false;
bool sensorDentroActivo = false;

// --- VARIABLES DE ESTADO PUERTA ---
int estadoAnteriorPuerta = -1; 

// Declaración de la función modificada para ser flexible
void enviarDatosAInternet(String tipoDato, String valorDato);

void setup() {
  Serial.begin(115200);
  
  pinMode(SENSOR_PIN_PUERTA, INPUT_PULLUP); 
  pinMode(TRIG_DENTRO, OUTPUT);
  pinMode(TRIG_FUERA, OUTPUT);
  pinMode(ECHO_DENTRO, INPUT);
  pinMode(ECHO_FUERA, INPUT);

  Serial.println("Iniciando conexión WiFi...");
  WiFi.begin("Pixel 8","password67"); 
  
  while(WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nCONECTADO");
  Serial.print("IP del ESP32: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // ------------------------------------------------------
  // 1. LÓGICA DEL SENSOR MAGNÉTICO (PUERTA)
  // ------------------------------------------------------
  int estadoActual = digitalRead(SENSOR_PIN_PUERTA); 
  
  if (estadoActual != estadoAnteriorPuerta) {
    Serial.print("Puerta: ");
    Serial.println(estadoActual == HIGH ? "ABIERTA" : "CERRADA");
    
    if (WiFi.status() == WL_CONNECTED) {
      // Enviamos con la etiqueta "estado_puerta"
      enviarDatosAInternet("estado_puerta", String(estadoActual));
      estadoAnteriorPuerta = estadoActual; 
    }
  }

  // ------------------------------------------------------
  // 2. LECTURA DE SENSORES ULTRASONICOS (Secuencial)
  // ------------------------------------------------------
  
  // --- SENSOR DENTRO ---
  digitalWrite(TRIG_DENTRO, LOW); 
  delayMicroseconds(2);
  digitalWrite(TRIG_DENTRO, HIGH);
  delayMicroseconds(10);          
  digitalWrite(TRIG_DENTRO, LOW);
  dActualDentro = pulseIn(ECHO_DENTRO, HIGH) / 59;
  
  delay(15); // Pequeña pausa para evitar interferencia entre sensores

  // --- SENSOR FUERA ---
  digitalWrite(TRIG_FUERA, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_FUERA, HIGH);
  delayMicroseconds(10);          
  digitalWrite(TRIG_FUERA, LOW);
  dActualFuera = pulseIn(ECHO_FUERA, HIGH) / 59;

  // ------------------------------------------------------
  // 3. LÓGICA DE DETECCIÓN DE PERSONAS (Entrada/Salida)
  // ------------------------------------------------------

  // A. Determinar si hay alguien frente a cada sensor
  // Filtramos ceros (errores) y distancias lejanas
  if (dActualDentro > 0 && dActualDentro < DISTANCIA_MAXIMA) {
    sensorDentroActivo = true;
  } else {
    sensorDentroActivo = false;
  }

  if (dActualFuera > 0 && dActualFuera < DISTANCIA_MAXIMA) {
    sensorFueraActivo = true;
  } else {
    sensorFueraActivo = false;
  }

  // B. Máquina de Estados (Secuencia)
  
  // CASO 1: Inicia secuencia de ENTRADA (Primero sensor FUERA)
  if (secuencia == 0 && sensorFueraActivo && !sensorDentroActivo) {
    secuencia = 1; 
    Serial.println("Secuencia: Alguien se acerca desde FUERA...");
  }

  // CASO 2: Inicia secuencia de SALIDA (Primero sensor DENTRO)
  if (secuencia == 0 && sensorDentroActivo && !sensorFueraActivo) {
    secuencia = 2; 
    Serial.println("Secuencia: Alguien se acerca desde DENTRO...");
  }

  // C. Confirmación del cruce
  
  // Si venía de fuera (1) y activa el de dentro -> ENTRÓ
  if (secuencia == 1 && sensorDentroActivo) {
    Serial.println("¡EVENTO: PERSONA ENTRÓ!");
    
    if (WiFi.status() == WL_CONNECTED) {
      // Enviamos etiqueta "movimiento" con valor "entrada"
      enviarDatosAInternet("movimiento", "entrada");
    }
    
    secuencia = 0; // Reiniciamos
    delay(1000);   // Pausa larga para no contar a la misma persona dos veces
  }

  // Si venía de dentro (2) y activa el de fuera -> SALIÓ
  if (secuencia == 2 && sensorFueraActivo) {
    Serial.println("¡EVENTO: PERSONA SALIÓ!");
    
    if (WiFi.status() == WL_CONNECTED) {
      // Enviamos etiqueta "movimiento" con valor "salida"
      enviarDatosAInternet("movimiento", "salida");
    }
    
    secuencia = 0; // Reiniciamos
    delay(1000);   // Pausa larga para no contar a la misma persona dos veces
  }

  // Reset por seguridad: Si ambos sensores dejan de detectar y la secuencia quedó a medias
  if (!sensorFueraActivo && !sensorDentroActivo) {
     secuencia = 0;
  }

  // Importante: Delay corto para que el loop sea rápido y no pierda personas caminando
  delay(50); 
}

// -----------------------------------------------------------------------------
// FUNCIÓN PARA ENVIAR DATOS (VERSIÓN CORREGIDA Y ROBUSTA)
// -----------------------------------------------------------------------------
void enviarDatosAInternet(String tipoDato, String valorDato) {
  // 1. Verificamos conexión antes de nada
  if(WiFi.status() != WL_CONNECTED){
    Serial.println("Error: WiFi desconectado, no se puede enviar.");
    return;
  }

  WiFiClient client;   // <--- ESTO ES NUEVO Y CRÍTICO
  HTTPClient http;
  
  // Usamos el cliente explícito
  http.begin(client, serverName);
  
  // Configuración para evitar que la conexión se quede "colgada"
  http.addHeader("Content-Type", "application/x-www-form-urlencoded"); 
  
  String httpRequestData = tipoDato + "=" + valorDato;
  
  Serial.print("Enviando POST (" + tipoDato + "): ");
  
  int httpResponseCode = http.POST(httpRequestData);
  
  if (httpResponseCode > 0) {
    Serial.print("Éxito. Código: ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("Error enviando. Código: ");
    Serial.println(httpResponseCode);
  }
  
  // Cerramos bien la conexión
  http.end(); 
  
  // Pequeño respiro para que el chip WiFi libere el socket
  delay(50); 
}