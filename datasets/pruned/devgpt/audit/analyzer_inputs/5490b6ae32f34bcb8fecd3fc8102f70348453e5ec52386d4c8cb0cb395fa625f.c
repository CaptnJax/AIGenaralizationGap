bool Wire_scan(uint8_t i2caddr) {
    return Wire_writeBytes(i2caddr, NULL, 0);
}