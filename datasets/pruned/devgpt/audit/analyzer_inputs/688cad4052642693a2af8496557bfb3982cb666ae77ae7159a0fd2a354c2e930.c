int CHUNK_GetNextRecord(CHUNK_RecordIterator *iterator, Record *record) {
    if (iterator->currentRecord >= iterator->chunk->recordsInChunk) {
        return -1;
    }
    iterator->currentRecord++;
    return 0;
}