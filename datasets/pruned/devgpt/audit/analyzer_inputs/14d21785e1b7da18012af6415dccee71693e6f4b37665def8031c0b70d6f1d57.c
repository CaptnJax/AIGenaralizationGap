void free_line(line_t line) {
    free(line.command);
    free(line.param_one);
    free(line.param_two);
}