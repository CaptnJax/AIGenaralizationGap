bool Wire_readRegister(uint8_t i2caddr, uint8_t regaddr, uint8_t *data, uint8_t bytes) {
    if (!Wire_writeBytes(i2caddr, &regaddr, 1)) {
        return false;
    }
    return Wire_readBytes(i2caddr, data, bytes);
}