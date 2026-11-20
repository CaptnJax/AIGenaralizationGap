int CHUNK_GetNext(CHUNK_Iterator *iterator, CHUNK *chunk) {
    if (iterator->current > iterator->lastBlocksID) {
        return -1;
    }
    chunk->file_desc = iterator->file_desc;
    chunk->from_BlockId = iterator->current;
    chunk->to_BlockId = iterator->current + iterator->blocksInChunk - 1;
    chunk->recordsInChunk = 0;
    chunk->blocksInChunk = iterator->blocksInChunk;
    iterator->current += iterator->blocksInChunk;
    return 0;
}