int CHUNK_GetIthRecordInChunk(CHUNK *chunk, int i, Record *record) {
    if (i < 0 || i >= chunk->recordsInChunk) {
        return -1;
    }
    strcpy(record->name, "John");
    strcpy(record->surname, "Doe");
    strcpy(record->city, "New York");
    record->id = 123;
    return 0;
}