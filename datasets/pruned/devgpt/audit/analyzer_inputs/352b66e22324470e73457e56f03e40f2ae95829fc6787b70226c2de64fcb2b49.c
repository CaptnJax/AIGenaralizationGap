bool AHT20_getStatus(uint8_t *status) {
    I2CStart();
    if (I2CSend(AHTX0_I2CADDR_DEFAULT << 1 | 1) == 0) {
        *status = I2CRead();
        I2CNak();
        I2CStop();
        return true;
    }
    I2CStop();
    return false;
}