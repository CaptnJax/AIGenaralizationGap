uint32_t search_record(const char *name) {
    pthread_mutex_lock(&hash_table.lock);
    hashRecord *current = hash_table.head;
    while (current != NULL && strcmp(current->name, name) != 0) {
        current = current->next;
    }
    uint32_t salary = 0;
    if (current != NULL && strcmp(current->name, name) == 0) {
        salary = current->salary;
    }
    pthread_mutex_unlock(&hash_table.lock);
    return salary;
}