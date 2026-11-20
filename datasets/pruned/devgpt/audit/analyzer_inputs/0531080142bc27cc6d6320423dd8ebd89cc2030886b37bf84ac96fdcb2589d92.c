bool Wire_scan(uint8_t i2caddr) {
    uint8_t ack_bit;
    I2CStart();
    ack_bit = I2CSend((i2caddr << 1) | 0);
    I2CStop();
    return (ack_bit == 0);
}