void Wire_readRegister(uint8_t i2caddr, uint8_t regaddr, uint8_t *data, uint8_t bytes) {
    uint8_t status;
    I2C_Start();
    status = I2C_SendByte((i2caddr << 1) | 0x00);
    if (status != I2C_ACK) {
        I2C_Stop();
        return;
    }
    status = I2C_SendByte(regaddr);
    if (status != I2C_ACK) {
        I2C_Stop();
        return;
    }
    I2C_Start();
    status = I2C_SendByte((i2caddr << 1) | 0x01);
    if (status != I2C_ACK) {
        I2C_Stop();
        return;
    }
    while (bytes > 0) {
        if (bytes == 1) {
            *data = I2C_RecvByte(I2C_NACK);
        } else {
            *data = I2C_RecvByte(I2C_ACK);
        }
        data++;
        bytes--;
    }
    I2C_Stop();
}