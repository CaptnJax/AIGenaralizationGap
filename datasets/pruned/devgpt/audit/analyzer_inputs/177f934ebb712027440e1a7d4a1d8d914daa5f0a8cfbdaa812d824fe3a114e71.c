void print_table() {
    pthread_rwlock_rdlock(&hash_table.lock);
    for (int i = 0; i < TABLE_SIZE; i++) {
        hashRecord *current = hash_table.table[i];
        while (current != NULL) {
            print_record(current);
            current = current->next;
        }
    }
    pthread_rwlock_unlock(&hash_table.lock);
}