int main() {
    int file_desc;
    char *filename = "example_file.txt";
    HP_CreateFile(filename);
    HP_OpenFile(filename, &file_desc);
    CHUNK_Iterator iterator = CHUNK_CreateIterator(file_desc, 10);
    HP_CloseFile(file_desc);
    return 0;
}