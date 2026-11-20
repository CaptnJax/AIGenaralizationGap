void processCharacters(char *input) {
    if (*input == '\0') {
        return;
    }
    if (*input == '/') {
        putchar(*(input + 1));
    }
    processCharacters(input + 1);
}