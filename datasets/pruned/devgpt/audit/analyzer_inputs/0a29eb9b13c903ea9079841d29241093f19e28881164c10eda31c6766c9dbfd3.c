char* format_with_commas(int num) {
    char buffer[50];
    sprintf(buffer, "%d", num);
    int length = strlen(buffer);
    int commaCount = (length - 1) / 3;
    int finalLength = length + commaCount;
    char *result = malloc(finalLength + 1);
    if (result == NULL) {
        return NULL;
    }
    int i = length - 1, j = finalLength;
    result[j--] = '\0';
    int commaPosition = 3;
    while (i >= 0) {
        result[j--] = buffer[i--];
        commaPosition--;
        if (commaPosition == 0 && j > 0) {
            result[j--] = ',';
            commaPosition = 3;
        }
    }
    return result;
}