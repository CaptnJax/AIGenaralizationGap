void Adafruit_HUSB238::selectPDO(HUSB238_PDOSelection pd) {
  Adafruit_I2CRegister pdoRegister = Adafruit_I2CRegister(i2c_dev, HUSB238_PDO_SELECT);
  Adafruit_I2CRegisterBits pdoBits = Adafruit_I2CRegisterBits(&pdoRegister, 4, 4);
  pdoBits.write(static_cast<uint8_t>(pd));
}