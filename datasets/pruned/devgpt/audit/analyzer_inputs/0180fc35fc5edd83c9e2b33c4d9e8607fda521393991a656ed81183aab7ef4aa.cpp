HUSB238_CurrentSetting Adafruit_HUSB238::getPDSrcCurrent() {
  Adafruit_I2CRegister pd0Register = Adafruit_I2CRegister(i2c_dev, HUSB238_PD_STATUS0);
  Adafruit_I2CRegisterBits srcCurrentBits = Adafruit_I2CRegisterBits(&pd0Register, 4, 0);
  return (HUSB238_CurrentSetting) srcCurrentBits.read();
}