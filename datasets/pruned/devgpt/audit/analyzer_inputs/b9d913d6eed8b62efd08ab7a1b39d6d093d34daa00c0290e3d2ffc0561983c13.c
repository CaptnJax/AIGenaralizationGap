int CHUNK_GetNextRecord(CHUNK_RecordIterator *iterator, Record *record) {
    if (iterator->currentRecord >= iterator->chunk->recordsInChunk) {
        return -1;
    }
    strcpy(record->name, iterator->chunk->records[iterator->currentRecord].name);
    strcpy(record->surname, iterator->chunk->records[iterator->currentRecord].surname);
    strcpy(record->city, iterator->chunk->records[iterator->currentRecord].city);
    record->id = iterator->chunk->records[iterator->currentRecord].id;
    iterator->currentRecord++;
    return 0;
}