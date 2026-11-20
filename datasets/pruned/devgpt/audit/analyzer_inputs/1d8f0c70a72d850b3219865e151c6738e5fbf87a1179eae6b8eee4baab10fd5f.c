void init_hash_table() {
    hash_table.head = NULL;
    pthread_rwlock_init(&hash_table.lock, NULL);
}