void print_table() {
    pthread_mutex_lock(&hash_table.lock);
    hashRecord *current = hash_table.head;
    while (current != NULL) {
        print_record(current);
        current = current->next;
    }
    pthread_mutex_unlock(&hash_table.lock);
}