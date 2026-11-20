uint32_t search_record(const char *name) {
    uint32_t hash_value = hash_function(name) % TABLE_SIZE;
    uint32_t salary = 0;
    pthread_rwlock_rdlock(&hash_table.lock);
    hashRecord *current = hash_table.table[hash_value];
    while (current != NULL && strcmp(current->name, name) != 0) {
        current = current->next;
    }
    if (current != NULL && strcmp(current->name, name) == 0) {
        salary = current->salary;
    }
    pthread_rwlock_unlock(&hash_table.lock);
    return salary;
}