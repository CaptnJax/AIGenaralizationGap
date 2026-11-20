void sort_Chunk(struct CHUNK* chunk) {
    int i, j;
    for (i = 0; i < chunk->recordsInChunk - 1; i++) {
        for (j = 0; j < chunk->recordsInChunk - i - 1; j++) {
            if (shouldSwap(&chunk->records[j], &chunk->records[j + 1])) {
                struct Record temp = chunk->records[j];
                chunk->records[j] = chunk->records[j + 1];
                chunk->records[j + 1] = temp;
            }
        }
    }
}