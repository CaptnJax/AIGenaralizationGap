void delete_record(const char *name) {
    uint32_t hash_value = hash_function(name) % TABLE_SIZE;
    pthread_rwlock_wrlock(&hash_table.lock);
    hashRecord *current = hash_table.table[hash_value];
    hashRecord *prev = NULL;
    while (current != NULL && strcmp(current->name, name) != 0) {
        prev = current;
        current = current->next;
    }
    if (current != NULL && strcmp(current->name, name) == 0) {
        if (prev == NULL) {
            hash_table.table[hash_value] = current->next;
        } else {
            prev->next = current->next;
        }
        free(current);
    }
    pthread_rwlock_unlock(&hash_table.lock);
}