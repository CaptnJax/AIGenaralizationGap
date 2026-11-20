bool readAHT20(float *temperature, float *humidity) {
    uint8_t cmd[3] = {AHTX0_CMD_TRIGGER, 0x33, 0x00};
    uint8_t data[6], status;
    uint32_t rawHumidity, rawTemperature;
    if (!Wire_writeBytes(AHTX0_I2CADDR_DEFAULT, cmd, 3)) {
        return false;
    }
    do {
        if (!AHT20_getStatus(&status)) {
            return false;
        }
        delay(10);
    } while (status & AHTX0_STATUS_BUSY);
    if (!Wire_readBytes(AHTX0_I2CADDR_DEFAULT, data, 6)) {
        return false;
    }
    rawHumidity = data[1];
    rawHumidity = (rawHumidity << 8) | data[2];
    rawHumidity = (rawHumidity << 4) | (data[3] >> 4);
    *humidity = ((float)rawHumidity * 100.0) / 0x100000;
    rawTemperature = (data[3] & 0x0F);
    rawTemperature = (rawTemperature << 8) | data[4];
    rawTemperature = (rawTemperature << 8) | data[5];
    *temperature = ((float)rawTemperature * 200.0 / 0x100000) - 50.0;
    return true;
}