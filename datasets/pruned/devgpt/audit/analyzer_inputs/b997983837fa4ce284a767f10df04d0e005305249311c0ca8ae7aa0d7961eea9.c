void CHUNK_Print(CHUNK chunk) {
    printf("File Descriptor: %d\n", chunk.file_desc);
    printf("From Block ID: %d\n", chunk.from_BlockId);
    printf("To Block ID: %d\n", chunk.to_BlockId);
    printf("Records in Chunk: %d\n", chunk.recordsInChunk);
    printf("Blocks in Chunk: %d\n", chunk.blocksInChunk);
    printf("\n");
}