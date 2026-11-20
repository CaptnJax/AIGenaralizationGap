int CHUNK_UpdateIthRecord(CHUNK *chunk, int i, Record record) {
    if (i < 0 || i >= chunk->recordsInChunk) {
        return -1;
    }
    return 0;
}