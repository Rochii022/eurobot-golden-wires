#include <WiFi.h>

void setup() {

  Serial.begin(115200);
  delay(2000);

  WiFi.mode(WIFI_STA);   // necesario para leer la MAC

  Serial.println();
  Serial.println("===== MAC ADDRESS =====");

  Serial.print("MAC: ");
  Serial.println(WiFi.macAddress());

}

void loop() {
}
