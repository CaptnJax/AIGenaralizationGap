void loop() {
  int command_id = esp_skainet_listen();
  switch (command_id) {
    case 1:
      digitalWrite(ledPin, HIGH);
      Serial.println("LED turned ON");
      break;
    case 2:
      digitalWrite(ledPin, LOW);
      Serial.println("LED turned OFF");
      break;
    default:
      break;
  }
}