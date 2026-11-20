unsigned int myfunc(const char *str, int additional_value) {
    unsigned int hash = 5381;
    int c;
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c + additional_value;
    }
    return hash;
}