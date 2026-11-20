void init_hash_table() {
    for (int i = 0; i < TABLE_SIZE; i++) {
        hash_table.table[i] = NULL;
    }
    pthread_rwlock_init(&hash_table.lock, NULL);
}