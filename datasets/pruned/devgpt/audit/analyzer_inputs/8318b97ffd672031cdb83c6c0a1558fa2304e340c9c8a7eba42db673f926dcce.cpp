bool Adafruit_HUSB238::isVoltageDetected(HUSB238_PDOSelection pd) {
  Adafruit_I2CRegister pdoRegister = Adafruit_I2CRegister(i2c_dev, SOME_REGISTER);
  Adafruit_I2CRegisterBits pdoBits = Adafruit_I2CRegisterBits(&pdoRegister, NUM_BITS, START_BIT);
  uint8_t detectedPdo = pdoBits.read();
  return (detectedPdo == static_cast<uint8_t>(pd));
}