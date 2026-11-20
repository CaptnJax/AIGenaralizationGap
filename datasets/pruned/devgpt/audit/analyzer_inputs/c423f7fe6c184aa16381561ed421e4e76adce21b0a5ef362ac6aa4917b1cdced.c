char base64dec_getc(const char **src) {
    while (**src && !isprint((unsigned char)**src))
        (*src)++;
    return **src ? *((*src)++) : '=';
}