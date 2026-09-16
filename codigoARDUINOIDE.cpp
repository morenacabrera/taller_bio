#include <SPI.h>
#include <Adafruit_MAX31855.h>

// Definición de pines para la interfaz SPI con el MAX31855
const int MAXCS = 10;
const int MAXDO = 12;
const int MAXCLK = 13;

// Inicialización del objeto sensor de temperatura
Adafruit_MAX31855 thermocouple(MAXCLK, MAXCS, MAXDO);

// Variables para controlar la frecuencia exacta de 1 Hz (1000 ms) sin bloquear el código
unsigned long tiempoAnterior = 0;
const long intervalo = 1000; 

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    delay(10); // Esperar a que se establezca el puerto serie con la PC
  }
  
  // Inicializar el módulo MAX31855
  if (!thermocouple.begin()) {
    Serial.println("ERROR: No se pudo iniciar el módulo MAX31855.");
    while (1) delay(10);
  }
}

void loop() {
  unsigned long tiempoActual = millis();

  // Control de tiempo para cumplir con la frecuencia de adquisición de 1 Hz
  if (tiempoActual - tiempoAnterior >= intervalo) {
    tiempoAnterior = tiempoActual;

    // Lectura de la temperatura de la termocupla en grados Celsius
    double temperatura = thermocouple.readCelsius();
    
    // Validación de errores (si la termocuple está desconectada o hay fallas)
    if (isnan(temperatura)) {
      Serial.println("ERROR: Termocupla desconectada o lectura inválida.");
    } else {
      // Envío de la lectura formateada hacia el puerto serie (para que lo lea Python)
      Serial.print("TEMP:");
      Serial.println(temperatura);
    }
  }
}