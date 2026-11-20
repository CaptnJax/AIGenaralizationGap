IoObject* hello(IoObject *self, IoObject *locals, IoMessage *m) {
    puts("Hello world!");
    return self;
}