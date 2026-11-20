void MyLibrary::interruptCallback() {
  if (instance) {
    instance->processInterrupt();
  }
}