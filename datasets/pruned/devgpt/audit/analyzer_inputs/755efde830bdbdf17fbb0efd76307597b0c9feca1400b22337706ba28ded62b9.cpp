void setup() {
  Serial.begin(115200);
  pinMode(ledPin, OUTPUT);
  esp_skainet_init();
  esp_skainet_add_command(commands[0], 1);
  esp_skainet_add_command(commands[1], 2);
  esp_skainet_start();
}