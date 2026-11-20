bool Adafruit_HUSB238::getAttached() {
  Adafruit_I2CRegister attachRegister = Adafruit_I2CRegister(i2c_dev, HUSB238_PD_STATUS0, 1, MSBFIRST);
  Adafruit_I2CRegisterBit attachBit = Adafruit_I2CRegisterBit(&attachRegister, 7);
  bool attachStatus = attachBit.read();
  return attachStatus;
}