void Adafruit_HUSB238::requestPDO() {
  Adafruit_I2CRegister goCommandRegister = Adafruit_I2CRegister(i2c_dev, HUSB238_GO_COMMAND);
  Adafruit_I2CRegisterBits requestBits = Adafruit_I2CRegisterBits(&goCommandRegister, 1, 0);
  requestBits.write(0b00001);
}