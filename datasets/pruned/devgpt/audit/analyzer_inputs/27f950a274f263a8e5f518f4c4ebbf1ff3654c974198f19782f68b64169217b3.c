FILE* open_input_file() {
    FILE* fp = fopen("commands.txt", "r");
    if(!fp) {
        fprintf(stderr, "[ERROR]: Could not open commands.txt file\n");
        exit(1);
    }
    return fp;
}