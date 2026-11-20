int read_brightness(const char* file_path) {
    struct stat sb;
    if (stat(file_path, &sb) == -1) {
        handle_error("stat");
    }
    FILE* file = fopen(file_path, "r");
    if (!file) {
        handle_error("fopen");
    }
    char file_contents[MAX_STR_LENGTH];
    if (fgets(file_contents, MAX_STR_LENGTH, file) == NULL) {
        handle_error("fgets");
    }
    fclose(file);
    return atoi(file_contents);
}