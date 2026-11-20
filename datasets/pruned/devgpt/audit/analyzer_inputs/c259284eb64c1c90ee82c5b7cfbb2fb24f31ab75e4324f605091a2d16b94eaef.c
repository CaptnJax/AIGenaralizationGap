void searchFiles(const char* searchPattern) {
    glob_t globResult;
    if (glob(searchPattern, 0, NULL, &globResult) != 0) {
        printf("Error matching files with pattern: %s\n", searchPattern);
        return;
    }
    for (size_t i = 0; i < globResult.gl_pathc; i++) {
        processFile(globResult.gl_pathv[i]);
    }
    globfree(&globResult);
}