CHUNK_Iterator CHUNK_CreateIterator(int fileDesc, int blocksInChunk) {
    CHUNK_Iterator iterator;
    iterator.file_desc = fileDesc;
    iterator.current = 1;
    iterator.lastBlocksID = 0;
    iterator.blocksInChunk = blocksInChunk;
    return iterator;
}