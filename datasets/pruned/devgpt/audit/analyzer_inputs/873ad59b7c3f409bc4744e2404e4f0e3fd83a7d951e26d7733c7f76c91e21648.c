int CHUNK_GetIthRecordInChunk(CHUNK *chunk, int i, Record *record) {
    if (i < 0 || i >= chunk->recordsInChunk) {
        return -1;
    }
    record->someField = i;
    return 0;
}