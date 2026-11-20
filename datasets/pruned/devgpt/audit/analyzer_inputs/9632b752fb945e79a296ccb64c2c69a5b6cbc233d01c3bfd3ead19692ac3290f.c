int CHUNK_UpdateIthRecord(CHUNK *chunk, int i, Record record) {
    if (i < 0 || i >= chunk->recordsInChunk) {
        return -1;
    }
    strcpy(chunk->records[i].name, record.name);
    strcpy(chunk->records[i].surname, record.surname);
    strcpy(chunk->records[i].city, record.city);
    chunk->records[i].id = record.id;
    return 0;
}