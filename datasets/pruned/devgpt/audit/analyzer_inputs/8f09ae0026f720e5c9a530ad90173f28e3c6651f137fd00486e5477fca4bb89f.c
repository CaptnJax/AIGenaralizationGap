void insert_record(const char *name, uint32_t salary) {
    uint32_t hash_value = hash_function(name) % TABLE_SIZE;
    pthread_rwlock_wrlock(&hash_table.lock);
    hashRecord *current = hash_table.table[hash_value];
    hashRecord *prev = NULL;
    while (current != NULL && strcmp(current->name, name) != 0) {
        prev = current;
        current = current->next;
    }
    if (current != NULL && strcmp(current->name, name) == 0) {
        current->salary = salary;
    } else {
        hashRecord *new_record = (hashRecord *)malloc(sizeof(hashRecord));
        if (new_record != NULL) {
            new_record->hash = hash_value;
            strncpy(new_record->name, name, 50);
            new_record->name[49] = '\0';
            new_record->salary = salary;
            new_record->next = NULL;
            if (prev == NULL) {
                hash_table.table[hash_value] = new_record;
            } else {
                prev->next = new_record;
            }
        }
    }
    pthread_rwlock_unlock(&hash_table.lock);
}