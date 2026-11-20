int CHUNK_GetNextRecord(CHUNK_RecordIterator *iterator, Record *record) {
    if (iterator->cursor >= iterator->chunk.recordsInChunk) {
        return -1;
    }
    strcpy(record->name, iterator->chunk.records[iterator->cursor].name);
    strcpy(record->surname, iterator->chunk.records[iterator->cursor].surname);
    strcpy(record->city, iterator->chunk.records[iterator->cursor].city);
    record->id = iterator->chunk.records[iterator->cursor].id;
    iterator->cursor++;
    return 0;
}