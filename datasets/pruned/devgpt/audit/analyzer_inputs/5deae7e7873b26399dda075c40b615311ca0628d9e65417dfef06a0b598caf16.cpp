bool Adafruit_HUSB238::getAttached() {
  Adafruit_I2CRegister attachRegister = Adafruit_I2CRegister(i2c_dev, HUSB238_PD_STATUS0, 1, MSBFIRST);
  uint8_t attachStatus = attachRegister.read();
  if (attachStatus & 0bXXXX) {
    return true;
  }
  return false;
}