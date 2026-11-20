int load_ssh_private_key(const char *filename, gcry_sexp_t *key) {
    FILE *fp = fopen(filename, "rb");
    if (fp == NULL) {
        fprintf(stderr, "Failed to open key file: %s\n", filename);
        return 0;
    }
    fseek(fp, 0, SEEK_END);
    long filesize = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    char *filecontent = (char *)malloc(filesize + 1);
    if (filecontent == NULL) {
        fclose(fp);
        fprintf(stderr, "Failed to allocate memory for key file\n");
        return 0;
    }
    fread(filecontent, 1, filesize, fp);
    filecontent[filesize] = '\0';
    fclose(fp);
    gcry_error_t err = gcry_sexp_new(key, filecontent, filesize, 0);
    free(filecontent);
    if (err) {
        fprintf(stderr, "Failed to load private key: %s\n", gcry_strerror(err));
        return 0;
    }
    return 1;
}