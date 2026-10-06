#include <TMCStepper.h>
#include <AccelStepper.h>

// Pin del LED interno del ESP32
#define LED_PIN 2

// Pines Motores
#define STEP_PIN1 12
#define DIR_PIN1  13
#define STEP_PIN2 26
#define DIR_PIN2  27
#define ENDSTOP_PIN 25

#define SERIAL_PORT Serial2 
#define R_SENSE 0.11f

// Direcciones UART
#define ADDR_MOTOR_1 0b00 // MS1=GND, MS2=GND
#define ADDR_MOTOR_2 0b01 // MS1=VCC, MS2=GND

// Constantes para movimiento
const float PASOS_POR_CM = 141.47; //(200* micropasos)/ (7.2 * pi)
const float PASOS_POR_GRADO = 21.68; // (17,8cm * PI * PASOS_POR_CM) / 360

const long posicionObjetivo = 6400;

TMC2209Stepper driver1(&SERIAL_PORT, R_SENSE, ADDR_MOTOR_1);
TMC2209Stepper driver2(&SERIAL_PORT, R_SENSE, ADDR_MOTOR_2);

AccelStepper stepper1(1, STEP_PIN1, DIR_PIN1);
AccelStepper stepper2(1, STEP_PIN2, DIR_PIN2);

void setup() { 
  Serial.begin(115200);
  delay(500);
  Serial.println(F("\n--- INICIANDO SISTEMA ---"));

  pinMode(LED_PIN, OUTPUT);
  pinMode(ENDSTOP_PIN, INPUT);

  // 1. Configuración UART y Drivers
  SERIAL_PORT.begin(115200, SERIAL_8N1, 16, 17);

  driver1.begin();
  driver1.pdn_disable(true);     // Prioridad a UART
  driver1.I_scale_analog(false); // Ignorar potenciómetro físico
  driver1.rms_current(1700);
  driver1.microsteps(16);
  driver1.toff(4);               // Tiempo de apagado óptimo para Nema 17
  driver1.blank_time(24);
  driver1.en_spreadCycle(true);  // Modo Torque (Más fuerza)
  driver1.pwm_autoscale(true);
  driver1.tbl(1); 

  driver2.begin();
  driver2.pdn_disable(true);     // Prioridad a UART
  driver2.I_scale_analog(false); // Ignorar potenciómetro físico
  driver2.rms_current(1700);
  driver2.microsteps(16);
  driver2.toff(4);               // Tiempo de apagado óptimo para Nema 17
  driver2.blank_time(24);
  driver2.en_spreadCycle(true);  // Modo Torque (Más fuerza)
  driver2.pwm_autoscale(true);
  driver2.tbl(1);
  
  Serial.print(F("Test conexion Driver 1 (debe ser 0): "));
  Serial.println(driver1.test_connection());

  Serial.print(F("Test conexion Driver 2 (debe ser 0): "));
  Serial.println(driver2.test_connection());

  stepper1.setCurrentPosition(0);
  stepper2.setCurrentPosition(0);
  
  // 2. Configuración AccelStepper
  stepper1.setMaxSpeed(8000);
  stepper1.setAcceleration(1500);

  stepper2.setMaxSpeed(8000);
  stepper2.setAcceleration(1500);

  delay(3000); // pequeña pausa
}

void loop() {
  /*
  avanzar(30);       // Avanza 30cm
  girar(90, true);   // Gira 90 grados a la izquierda
  avanzar(60);       // Avanza 20cm
  girar(180, false); // Media vuelta a la derecha
  retroceder(10);    // Vuelve 10cm atrás
  */
  
  setVelocidad(6000,1200);
  retroceder(55);
  setVelocidad(5000,1000);
  girar(90, false);   // Gira 90 grados a la izquierda
  avanzar(10);
  girar(180, false);
  avanzar(12);
  girar(90, false);
  delay(1000);
}

void avanzar(float cm) {
  long pasos = cm * PASOS_POR_CM;
  Serial.print(F("Avanzando cm: ")); Serial.println(cm);
  digitalWrite(LED_PIN, HIGH);
  stepper1.move(-pasos);
  stepper2.move(pasos);
  ejecutar();
}

void retroceder(float cm) {
  long pasos = cm * PASOS_POR_CM;
  digitalWrite(LED_PIN, LOW);
  Serial.print(F("Retrocediendo cm: ")); Serial.println(cm);
  stepper1.move(pasos);
  stepper2.move(-pasos);
  ejecutar();
}

void girar(float grados, bool izquierda) {
  long pasosGiro = grados * PASOS_POR_GRADO;
  Serial.print(F("Girando grados: ")); Serial.println(grados);
  
  if (izquierda) {
    stepper1.move(pasosGiro);
    stepper2.move(pasosGiro);
  } else {
    stepper1.move(-pasosGiro);
    stepper2.move(-pasosGiro);
  }
  ejecutar();
}

void ejecutar() {
  while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
    stepper1.run();
    stepper2.run();
  }
  delay(200);
}

void setVelocidad(float velocidad, float aceleracion) {
  stepper1.setMaxSpeed(velocidad);
  stepper1.setAcceleration(aceleracion);

  stepper2.setMaxSpeed(velocidad);
  stepper2.setAcceleration(aceleracion);
}
