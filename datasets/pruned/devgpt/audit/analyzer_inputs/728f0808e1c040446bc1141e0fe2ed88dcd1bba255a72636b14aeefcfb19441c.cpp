MyLibrary::MyLibrary(int interruptPin, int i2cAddress)
    : interruptPin(interruptPin), i2cAddress(i2cAddress) {
  instance = this;
}