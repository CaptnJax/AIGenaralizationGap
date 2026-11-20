int main() {
    int num = 7000000;
    char *formattedNum = format_with_commas(num);
    if (formattedNum) {
        printf("%s\n", formattedNum);
        free(formattedNum);
    } else {
        printf("Memory allocation failed.\n");
    }
    return 0;
}