line_t parse_line(char* buffer) {
    line_t line;
    char* token = strtok(buffer, ",");
    if(!token) {
        fprintf(stderr, "[ERROR]: Failed to tokenize input\n");
        exit(1);
    }
    line.command = strdup(token);
    token = strtok(NULL, ",");
    if(!token) {
        fprintf(stderr, "[ERROR]: Failed to tokenize input\n");
        exit(1);
    }
    line.param_one = strdup(token);
    token = strtok(NULL, ",");
    if(!token) {
        fprintf(stderr, "[ERROR]: Failed to tokenize input\n");
        exit(1);
    }
    line.param_two = strdup(token);
    return line;
}