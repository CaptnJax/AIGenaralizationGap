CHUNK_RecordIterator CHUNK_CreateRecordIterator(CHUNK *chunk) {
    CHUNK_RecordIterator iterator;
    iterator.chunk = chunk;
    iterator.currentRecord = 0;
    return iterator;
}