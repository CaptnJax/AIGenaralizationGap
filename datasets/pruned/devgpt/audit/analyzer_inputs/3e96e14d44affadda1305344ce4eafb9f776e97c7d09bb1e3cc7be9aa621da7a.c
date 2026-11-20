void init_hash_table() {
    hash_table.head = NULL;
    pthread_create(&hash_table.lock, NULL, start_routine, arg);
}