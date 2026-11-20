void print_table() {
    pthread_rwlock_rdlock(&hash_table.lock);
    hashRecord *current = hash_table.head;
    while (current != NULL) {
        print_record(current);
        current = current->next;
    }
    pthread_rwlock_unlock(&hash_table.lock);
}