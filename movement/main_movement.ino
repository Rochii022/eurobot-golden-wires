#include <TMCStepper.h>
#include <AccelStepper.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// ================== CONFIGURACIÓN PINES ==================
#define LED_PIN 2
#define STEP_PIN1 12
#define DIR_PIN1  13
#define STEP_PIN2 26
#define DIR_PIN2  27

#define FINAL_CARRERA 4
#define INTERRUPTOR 14

const byte CMD_AZUL = 0xB1;
const byte CMD_AMARILLO = 0xB2;
const byte CMD_OK = 0x00;
const byte CMD_READY = 0x99;
const byte CMD_FOTO = 'C'; // Carácter 'C' para pedir foto

const uint8_t ID_AZUL = 36;
const uint8_t ID_AMARILLO = 47;
const uint8_t ID_AUSENTE = 0;

// Variable para guardar lo que lee la Raspberry
uint8_t piezasDetectadas[4] = {0, 0, 0, 0};

const int NUM_SENSORES = 5;
const int trigPins[NUM_SENSORES] = {33, 25, 23, 19, 18}; 
const int echoPins[NUM_SENSORES] = {32, 35, 34, 39, 36}; 

#define SERIAL_PORT Serial2 
#define R_SENSE 0.11f
#define ADDR_MOTOR_1 0b00
#define ADDR_MOTOR_2 0b01

// ================== VARIABLES GLOBALES ==================
const float PASOS_POR_CM = 141.47;
const float PASOS_POR_GRADO = 21.97;

// Distancia de cada sensor y una bandera general
volatile float distanciasGlobales[NUM_SENSORES] = {100.0, 100.0, 100.0, 100.0, 100.0};
volatile bool peligroInminente = false; 

TMC2209Stepper driver1(&SERIAL_PORT, R_SENSE, ADDR_MOTOR_1);
TMC2209Stepper driver2(&SERIAL_PORT, R_SENSE, ADDR_MOTOR_2);

AccelStepper stepper1(1, STEP_PIN1, DIR_PIN1);
AccelStepper stepper2(1, STEP_PIN2, DIR_PIN2);

// Instancia del controlador (dirección por defecto 0x40)
Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver();

#define SERVOMIN  150 // Pulso mínimo (0°)
#define SERVOMAX  600 // Pulso máximo (180°)
#define FREQUENCY 50  // Frecuencia para servos analógicos (50Hz)

void tareaUltrasonidos(void * param){
  while(1){
    bool detectadoAhora = false;

    // Escanear los 5 sensores secuencialmente
    for (int i = 0; i < NUM_SENSORES; i++) {
      digitalWrite(trigPins[i], LOW);
      delayMicroseconds(2);
      digitalWrite(trigPins[i], HIGH);
      delayMicroseconds(10);
      digitalWrite(trigPins[i], LOW);

      // Timeout de 5000us para evitar que 5 sensores bloqueen el loop si no hay ecos
      // 5000us alcanzan de sobra para detectar cosas a < 80 cm
      long duration = pulseIn(echoPins[i], HIGH, 5000);
      
      if (duration == 0) {
        distanciasGlobales[i] = 100.0; // Si no hay eco, asumimos que está libre (lejos)
      } else {
        distanciasGlobales[i] = duration * 0.034 / 2;
      }

      // Si CUALQUIER sensor detecta algo a menos de 15cm
      if (distanciasGlobales[i] > 0 && distanciasGlobales[i] < 15.0) {
        detectadoAhora = true;
      }
      
      delay(2); // Pequeña pausa para que los ecos no se crucen entre sensores
    }

    peligroInminente = detectadoAhora;

    // Control visual del LED
    if (peligroInminente) digitalWrite(LED_PIN, HIGH);
    else digitalWrite(LED_PIN, LOW);

    // Pausa general de la tarea
    vTaskDelay(30 / portTICK_PERIOD_MS); 
  }
}

void setup() { 
  Serial.begin(115200);
  delay(1000);

  pinMode(LED_PIN, OUTPUT);
  pinMode(INTERRUPTOR, INPUT_PULLUP);
  pinMode(FINAL_CARRERA, INPUT_PULLUP);

  // Inicializar pines de los 5 sensores
  for (int i = 0; i < NUM_SENSORES; i++) {
    pinMode(trigPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);
  }

  // Configuración UART Drivers
  SERIAL_PORT.begin(115200, SERIAL_8N1, 16, 17);

  driver1.begin();
  driver1.pdn_disable(true);
  driver1.I_scale_analog(false);
  driver1.rms_current(1700);
  driver1.microsteps(16);
  driver1.en_spreadCycle(true);
  driver1.pwm_autoscale(true);

  driver2.begin();
  driver2.pdn_disable(true);
  driver2.I_scale_analog(false);
  driver2.rms_current(1700);
  driver2.microsteps(16);
  driver2.en_spreadCycle(true);
  driver2.pwm_autoscale(true);

  stepper1.setMaxSpeed(8000);
  stepper1.setAcceleration(1500);
  stepper2.setMaxSpeed(8000);
  stepper2.setAcceleration(1500);

  // Crear tarea del sensor en el Core 0
  xTaskCreatePinnedToCore(tareaUltrasonidos, "TaskSensor", 4000, NULL, 1, NULL, 0);

  pca.begin();
  pca.setPWMFreq(FREQUENCY);

  bool pi_ready = false;
  while (!pi_ready) {
    if (Serial.available() > 0) {
      byte incoming = Serial.read();
      if (incoming == CMD_READY) {
        pi_ready = true;
      }
    }
    delay(100); // Pequeña pausa para no saturar la ESP32
  }

  Serial.write(CMD_OK);

  Serial.println("Sistema de 5 sensores listo. Iniciando en 3 segundos...");
  delay(1000);
}

void loop() {
  while(digitalRead(FINAL_CARRERA) != LOW){

    if(digitalRead(INTERRUPTOR) == HIGH){
    Serial.write(CMD_AMARILLO);
    } else {
    Serial.write(CMD_AZUL);
    }
  }
  Serial.write(0x00);
  setVelocidad(6000, 1200);  
  
  retroceder(28);
  girar(90, true);
  avanzar(20);
  girar(90, true);
  avanzar(48);
  retroceder(10);
  girar(90, true);
  avanzar(20);
  girar(90, false);
  avanzar(15);
  girar(90, true);
  avanzar(80);
  retroceder(5);
  girar(90, false);
  avanzar(55);
  retroceder(5);
  girar(90, false);
  avanzar(15);
  girar(90, true);
  avanzar(25);
  girar(90, false);
  //ESPERAR SIMAS 
  setVelocidad(8000, 1500);
  avanzar(100);
  delay(10000000000000000000000000);
}

// ================== FUNCIONES DE MOVIMIENTO ==================

void ejecutar() {
  while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
    
    // Si la bandera global de peligro está activa
    if (peligroInminente) {
      Serial.println("OBSTÁCULO DETECTADO - FRENADA EN SECO");
      
      // 1. Guardar exactamente cuántos pasos faltaban para terminar el movimiento
      long p1 = stepper1.distanceToGo();
      long p2 = stepper2.distanceToGo();

      // 2. FRENADA EN SECO: Establecemos el objetivo en la posición actual exacta.
      // Esto elimina la curva de desaceleración al instante.
      stepper1.moveTo(stepper1.currentPosition());
      stepper2.moveTo(stepper2.currentPosition());
      
      // 3. Forzamos la velocidad actual a 0 por seguridad
      stepper1.setSpeed(0);
      stepper2.setSpeed(0);

      // 4. Esperar hasta que todos los sensores estén limpios
      while(peligroInminente) {
        delay(50);
      }

      Serial.println("Camino libre - Reanudando");
      
      // 5. Cargar de nuevo la distancia que faltaba (como movimiento relativo)
      stepper1.move(p1);
      stepper2.move(p2);
    }

    stepper1.run();
    stepper2.run();
  }
}

void avanzar(float cm) {
  long pasos = cm * PASOS_POR_CM;
  stepper1.move(-pasos);
  stepper2.move(pasos);
  ejecutar();
}

void retroceder(float cm) {
  long pasos = cm * PASOS_POR_CM;
  stepper1.move(pasos);
  stepper2.move(-pasos);
  ejecutar();
}

void girar(float grados, bool izquierda) {
  long pasosGiro = grados * PASOS_POR_GRADO;
  if (izquierda) {
    stepper1.move(pasosGiro);
    stepper2.move(pasosGiro);
  } else {
    stepper1.move(-pasosGiro);
    stepper2.move(-pasosGiro);
  }
  ejecutar();
}

void setVelocidad(float velocidad, float aceleracion) {
  stepper1.setMaxSpeed(velocidad);
  stepper1.setAcceleration(aceleracion);
  stepper2.setMaxSpeed(velocidad);
  stepper2.setAcceleration(aceleracion);
}

// Función para mover un servo a un ángulo (0 a 180)
void moverServo(uint8_t num, int angulo) {
  int pulso = map(angulo, 0, 180, SERVOMIN, SERVOMAX);
  pca.setPWM(num, 0, pulso);
}

// Función para actuar como Digital ON/OFF (Válvula)
void controlarValvula(uint8_t num, bool estado) {
  if (estado) {
    pca.setPWM(num, 4096, 0); // ON (Totalmente encendido)
  } else {
    pca.setPWM(num, 0, 4096); // OFF (Totalmente apagado)
  }
}

void mueve_brazo(){
  controlarValvula(15, true);
  controlarValvula(10, true);
  delay(500);
  moverServo(0, 170);
  delay(2000);
  moverServo(1, 50);
  delay(2000);
  moverServo(0, 30);
  delay(2000);
  moverServo(1, 150);
  delay(2000);
  controlarValvula(15, false);
  controlarValvula(10, false);
  delay(2000);
}

// ================== COMUNICACIÓN CÁMARA ==================

bool esperarRespuestaRaspberry() {
  // 1. Limpiamos el buffer por si hay datos viejos
  while(Serial.available()) Serial.read(); 

  // 2. Pedimos la foto
  Serial.write(CMD_FOTO); 
  
  // 3. Espera bloqueante con Timeout de 4 segundos
  unsigned long startWait = millis();
  while (Serial.available() < 7) { 
    if (millis() - startWait > 4000) { 
      Serial.println("Error: Timeout - Raspberry no responde");
      return false; 
    }
  }

  // 4. Leer y validar el paquete (Cabecera 0xAA, Len 4, Datos, Fin 0x55)
  if (Serial.read() == 0xAA) { 
    uint8_t len = Serial.read();
    
    for (int i = 0; i < len; i++) {
      if (i < 4) piezasDetectadas[i] = Serial.read();
      else Serial.read(); // Vaciamos si envia mas de 4 por error
    }

    uint8_t footer = Serial.read();
    if (footer == 0x55) {
      return true; // Éxito
    }
  }
  
  return false; // Paquete erróneo
}

void pedirFotoYEsperar() {
  Serial.println(">> Solicitando foto a Raspberry...");
  
  // El código se detiene en este 'if' hasta que la Raspberry contesta o da timeout
  if (esperarRespuestaRaspberry()) {
    Serial.println(">> ¡Respuesta Recibida!");
    for (int i = 0; i < 4; i++) {
      Serial.print("   Zona "); Serial.print(i + 1); Serial.print(": ");
      if (piezasDetectadas[i] == ID_AZUL) {
        Serial.println("AZUL");
        digitalWrite(LED_PIN, HIGH);
        delay(2000);
        digitalWrite(LED_PIN, LOW);
        delay(2000);
      }
      else if (piezasDetectadas[i] == ID_AMARILLO) {
        Serial.println("AMARILLO");
        digitalWrite(LED_PIN, HIGH);
        delay(500);
        digitalWrite(LED_PIN, LOW);
        delay(500);
        digitalWrite(LED_PIN, HIGH);
        delay(500);
        digitalWrite(LED_PIN, LOW);
        delay(500);
        digitalWrite(LED_PIN, HIGH);
        delay(500);
        digitalWrite(LED_PIN, LOW);
        delay(500);
        digitalWrite(LED_PIN, HIGH);
        delay(500);
        digitalWrite(LED_PIN, LOW);
        delay(500);
      }
      else Serial.println("AUSENTE");
    }
  } else {
    Serial.println(">> Fallo al recibir los datos de las piezas.");
  }
}

void coger_piezas(int num, int piezas[4]){
  if(num == 4){
    controlarValvula(15, true);
    controlarValvula(10, true);
    controlarValvula(12, true);
    controlarValvula(13, true);
  }
  
  delay(500);
  moverServo(0, 60);
  delay(2000);
  moverServo(0, 100);
  delay(2000);
}