// wearable.ino - GlassesSense v2 firmware. The code is in app.cpp (see its header).

void app_setup();
void app_loop();

void setup() {
  Serial.begin(115200);   // Debug line when USB is attached
  app_setup();
}

void loop() { app_loop(); }
