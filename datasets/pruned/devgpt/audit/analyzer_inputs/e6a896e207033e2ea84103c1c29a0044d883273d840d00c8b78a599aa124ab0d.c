int main(int argc, const char *argv[]) {
    IoState *self = IoState_new();
    IoObject *lobby = IoState_lobby(self);
    IoState_init(self);
    IoMethodTable methodTable[] = {{"hello", hello}, {NULL, NULL}};
    IoObject_addMethodTable_(lobby, methodTable);
    IoState_doCString_(self, "hello();");
    IoState_free(self);
    return 0;
}