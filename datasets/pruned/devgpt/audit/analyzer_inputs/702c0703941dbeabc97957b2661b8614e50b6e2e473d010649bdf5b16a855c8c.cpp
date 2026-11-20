HUSB238_PDOSelection Adafruit_HUSB238::getSelectedPDO() {
  Adafruit_I2CRegister pdoRegister = Adafruit_I2CRegister(i2c_dev, HUSB238_PDO_SELECT);
  Adafruit_I2CRegisterBits pdoBits = Adafruit_I2CRegisterBits(&pdoRegister, 4, 4);
  return (HUSB238_PDOSelection) pdoBits.read();
}