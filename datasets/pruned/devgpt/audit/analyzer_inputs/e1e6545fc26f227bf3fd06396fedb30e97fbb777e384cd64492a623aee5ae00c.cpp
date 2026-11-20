void Adafruit_HUSB238::getSourceCapabilities() {
  Adafruit_I2CRegister goCommandRegister = Adafruit_I2CRegister(i2c_dev, HUSB238_GO_COMMAND);
  Adafruit_I2CRegisterBits capabilitiesBits = Adafruit_I2CRegisterBits(&goCommandRegister, 5, 0);
  capabilitiesBits.write(0b00100);
}