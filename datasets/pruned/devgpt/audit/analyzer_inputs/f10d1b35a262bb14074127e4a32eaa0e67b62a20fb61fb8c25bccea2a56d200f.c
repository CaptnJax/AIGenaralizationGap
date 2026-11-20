int main() {
    int file_desc;
    char *filename = "example_file.txt";
    HP_CreateFile(filename);
    HP_OpenFile(filename, &file_desc);
    CHUNK_Iterator chunkIterator = CHUNK_CreateIterator(file_desc, 10);
    CHUNK chunk;
    while (CHUNK_GetNext(&chunkIterator, &chunk) == 0) {
        CHUNK_Print(chunk);
        Record record;
        CHUNK_RecordIterator recordIterator = CHUNK_CreateRecordIterator(&chunk);
        while (CHUNK_GetNextRecord(&recordIterator, &record) == 0) {
            printf("Record: %d\n", record.someField);
        }
    }
    HP_CloseFile(file_desc);
    return 0;
}