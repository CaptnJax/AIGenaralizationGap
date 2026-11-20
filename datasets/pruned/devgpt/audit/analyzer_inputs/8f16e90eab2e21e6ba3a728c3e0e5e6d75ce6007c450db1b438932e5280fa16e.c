void *start_routine(void *arg) {
    pthread_rwlock_init(&hash_table.lock, NULL);
    return NULL;
}