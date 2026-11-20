void checkSwitches() {
  static unsigned long lastSW4Press = 0;
  static bool servoActivated = false;
  unsigned long currentMillis = millis();
  if (digitalRead(sw1) == LOW) {
    Serial.println("SW1 pressed");
  }
  if (digitalRead(sw2) == LOW) {
    Serial.println("SW2 pressed");
    myservo.write(180);
    servoActivated = true;
  }
  if (digitalRead(sw3) == LOW) {
    Serial.println("SW3 pressed");
    myservo.write(0);
    servoActivated = false;
  }
  if (digitalRead(sw4) == LOW) {
    Serial.println("SW4 pressed");
    if (currentMillis - lastSW4Press >= 3000 && !servoActivated) {
      myservo.write(180);
      lastSW4Press = currentMillis;
      servoActivated = true;
    }
    else if (currentMillis - lastSW4Press >= 3000 && servoActivated) {
      myservo.write(0);
      lastSW4Press = currentMillis;
      servoActivated = false;
    }
  }
}