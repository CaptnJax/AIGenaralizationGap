void Adafruit_HUSB238::reset() {
  Adafruit_I2CRegister goCommandRegister = Adafruit_I2CRegister(i2c_dev, HUSB238_GO_COMMAND);
  Adafruit_I2CRegisterBits resetBits = Adafruit_I2CRegisterBits(&goCommandRegister, 5, 0);
  resetBits.write(0b10000);
}