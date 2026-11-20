int main(int argc, const char *argv[]) {
    IoState *self = IoState_new();
    IoState_init(self);
    IoObject *method = IoState_protoWithInitFunction(self, (IoStateProtoFunc)hello);
    IoState_registerProtoWithFunc_(self, method, hello);
    IoState_rawDoCString_(self, "hello();");
    IoState_free(self);
    return 0;
}