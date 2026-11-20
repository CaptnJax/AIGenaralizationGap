FILE* open_output_file() {
    FILE* fp = fopen("output.txt", "w");
    if(!fp) {
        fprintf(stderr, "[ERROR]: Could not create or open the output.txt file\n");
        exit(1);
    }
    return fp;
}