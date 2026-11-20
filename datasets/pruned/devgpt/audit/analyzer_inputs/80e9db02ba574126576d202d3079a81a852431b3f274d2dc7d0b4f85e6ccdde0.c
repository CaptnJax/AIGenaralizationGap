void delete_record(const char *name) {
    pthread_mutex_lock(&hash_table.lock);
    hashRecord *current = hash_table.head;
    hashRecord *prev = NULL;
    while (current != NULL && strcmp(current->name, name) != 0) {
        prev = current;
        current = current->next;
    }
    if (current != NULL && strcmp(current->name, name) == 0) {
        if (prev == NULL) {
            hash_table.head = current->next;
        } else {
            prev->next = current->next;
        }
        free(current);
    }
    pthread_mutex_unlock(&hash_table.lock);
}