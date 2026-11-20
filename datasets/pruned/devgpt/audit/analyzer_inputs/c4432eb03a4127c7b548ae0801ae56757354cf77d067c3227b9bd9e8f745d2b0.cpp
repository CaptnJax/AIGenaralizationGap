HUSB238_VoltageSetting Adafruit_HUSB238::getPDSrcVoltage() {
  Adafruit_I2CRegister pd0Register = Adafruit_I2CRegister(i2c_dev, HUSB238_PD_STATUS0);
  Adafruit_I2CRegisterBits srcVoltageBits = Adafruit_I2CRegisterBits(&pd0Register, 4, 4);
  return (HUSB238_VoltageSetting) srcVoltageBits.read();
}