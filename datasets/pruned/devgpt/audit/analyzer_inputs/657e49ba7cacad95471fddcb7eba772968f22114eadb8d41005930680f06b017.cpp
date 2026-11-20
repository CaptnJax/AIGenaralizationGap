void loop() {
     int vinValue = analogRead(vinPin);
     float voltage = vinValue / 4095.0 * 3.3;
     Serial.print("Vin Voltage: ");
     Serial.print(voltage);
     Serial.println("V");
     delay(1000);
   }