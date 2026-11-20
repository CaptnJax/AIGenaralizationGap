int main() {
    int file_desc;
    char *filename = "example_file.txt";
    HP_CreateFile(filename);
    HP_OpenFile(filename, &file_desc);
    CHUNK_Iterator iterator = CHUNK_CreateIterator(file_desc, 10);
    CHUNK chunk;
    while (CHUNK_GetNext(&iterator, &chunk) == 0) {
        printf("File Descriptor: %d\n", chunk.file_desc);
        printf("From Block ID: %d\n", chunk.from_BlockId);
        printf("To Block ID: %d\n", chunk.to_BlockId);
        printf("Records in Chunk: %d\n", chunk.recordsInChunk);
        printf("Blocks in Chunk: %d\n", chunk.blocksInChunk);
        printf("\n");
    }
    HP_CloseFile(file_desc);
    return 0;
}