void write_brightness(const char* file_path, int brightness) {
    FILE* file = fopen(file_path, "w");
    if (!file) {
        handle_error("fopen");
    }
    fprintf(file, "%d", brightness);
    fclose(file);
}