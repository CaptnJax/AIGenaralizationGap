void init_hash_table() {
    pthread_create(&hash_table.lock, NULL, start_routine, NULL);
}