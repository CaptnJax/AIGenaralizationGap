void checkSwitches() {
  static unsigned long lastSW4Press = 0;
  static bool servoActivated = false;
  static unsigned long buzzerStartTime = 0;
  unsigned long currentMillis = millis();
  if (digitalRead(sw1) == LOW) {
    Serial.println("SW1 pressed");
  }
  if (digitalRead(sw2) == LOW) {
    Serial.println("SW2 pressed");
    myservo.write(180);
    servoActivated = true;
    buzzerStartTime = currentMillis;
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
      buzzerStartTime = currentMillis;
    }
    else if (currentMillis - lastSW4Press >= 3000 && servoActivated) {
      myservo.write(0);
      lastSW4Press = currentMillis;
      servoActivated = false;
    }
  }
  if (servoActivated && myservo.read() == 180 && currentMillis - buzzerStartTime <= 500) {
    digitalWrite(buzzer, HIGH);
  } else {
    digitalWrite(buzzer, LOW);
  }
}