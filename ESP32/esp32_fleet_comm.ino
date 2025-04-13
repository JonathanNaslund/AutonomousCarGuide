#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

WiFiUDP udp;
const int udpPort = 4210;
char incomingPacket[256];

void setup() {
  Serial.begin(115200);
  WiFi.begin("YOUR_SSID", "YOUR_PASS");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("WiFi connected");
  udp.begin(udpPort);
}

void loop() {
  // 1. Check UART for new message from Pi
  if (Serial.available()) {
    String msg = Serial.readStringUntil('\n');
    udp.beginPacket("255.255.255.255", udpPort); // broadcast
    udp.print(msg);
    udp.endPacket();
  }

  // 2. Check for incoming UDP from others
  int len = udp.parsePacket();
  if (len) {
    udp.read(incomingPacket, 256);
    incomingPacket[len] = '\0';
    Serial.println(incomingPacket); // Send to Pi over UART
  }

  delay(10);
}
