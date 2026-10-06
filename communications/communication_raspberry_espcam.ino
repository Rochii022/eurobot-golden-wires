const int LED_PIN = 2;
const byte CMD_AZUL = 0xB1;
const byte CMD_AMARILLO = 0xB2;
const byte CMD_OK = 0x00;
const byte CMD_READY = 0x99;
const byte CMD_FOTO = 'C'; // Carácter 'C' para pedir foto

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  
  bool pi_ready = false;
  while (!pi_ready) {
    if (Serial.available() > 0) {
      byte incoming = Serial.read();
      if (incoming == CMD_READY) {
        pi_ready = true; // Una vez recibida la señal salimos del bucle
      }
    }
    delay(100); // Pequeña pausa para no saturar la ESP32
  }
  // SECUENCIA DE INICIO (15 segundos)
  digitalWrite(LED_PIN, HIGH);
  delay(1000);
  digitalWrite(LED_PIN, LOW);

  // 1. Esperar 5 seg y mandar AZUL
  delay(5000);
  Serial.write(CMD_AZUL);
  
  // 2. Esperar 5 seg y mandar AMARILLO
  delay(5000);
  Serial.write(CMD_AMARILLO);
  
  // 3. Esperar 5 seg y mandar OK
  delay(5000);
  Serial.write(CMD_OK);
  
}

void loop() {
  // BUCLE DE FOTOS (Cada 5 segundos)
  delay(5000);
  
  // Pedir foto
  Serial.write(CMD_FOTO);
  
  // Leer respuesta (Array de ArUcos)
  if (Serial.available() > 0) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
  }
}