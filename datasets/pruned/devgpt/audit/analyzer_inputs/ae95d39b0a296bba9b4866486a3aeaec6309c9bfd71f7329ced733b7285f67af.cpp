HUSB238_CurrentSetting Adafruit_HUSB238::currentDetected(HUSB238_PDOSelection pd) {
  uint8_t registerAddress;
  switch(pd) {
    case PDO_5V:
      registerAddress = HUSB238_SRC_PDO_5V;
      break;
    case PDO_9V:
      registerAddress = HUSB238_SRC_PDO_9V;
      break;
    case PDO_12V:
      registerAddress = HUSB238_SRC_PDO_12V;
      break;
    case PDO_15V:
      registerAddress = HUSB238_SRC_PDO_15V;
      break;
    case PDO_18V:
      registerAddress = HUSB238_SRC_PDO_18V;
      break;
    case PDO_20V:
      registerAddress = HUSB238_SRC_PDO_20V;
      break;
    default:
      return CURRENT_UNKNOWN;
  }
  Adafruit_I2CRegister pdoRegister = Adafruit_I2CRegister(i2c_dev, registerAddress);
  Adafruit_I2CRegisterBits currentBits = Adafruit_I2CRegisterBits(&pdoRegister, 4, 0);
  return (HUSB238_CurrentSetting) currentBits.read();
}