int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <up|down>\n", argv[0]);
        return EXIT_FAILURE;
    }
    int current_brightness = read_brightness(FILE_PATH);
    int new_brightness;
    if (strcmp(argv[1], "up") == 0) {
        printf("Brightness up\n");
        new_brightness = current_brightness + BRIGHTNESS_INCREMENT;
    } else if (strcmp(argv[1], "down") == 0) {
        printf("Brightness down\n");
        new_brightness = current_brightness - BRIGHTNESS_INCREMENT;
    } else {
        printf("Unknown option: %s\n", argv[1]);
        new_brightness = current_brightness;
    }
    if (new_brightness > MAX_BRIGHTNESS) {
        new_brightness = MAX_BRIGHTNESS;
    } else if (new_brightness < MIN_BRIGHTNESS) {
        new_brightness = MIN_BRIGHTNESS;
    }
    printf("Current brightness: %d\n", current_brightness);
    printf("New brightness: %d\n", new_brightness);
    write_brightness(FILE_PATH, new_brightness);
    return EXIT_SUCCESS;
}