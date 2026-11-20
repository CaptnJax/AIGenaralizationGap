void insert_record(const char *name, uint32_t salary) {
    uint32_t hash_value = hash_function(name);
    pthread_rwlock_wrlock(&hash_table.lock);
    hashRecord *new_record = (hashRecord *)malloc(sizeof(hashRecord));
    if (new_record != NULL) {
        new_record->hash = hash_value;
        strncpy(new_record->name, name, 50);
        new_record->name[49] = '\0';
        new_record->salary = salary;
        new_record->next = NULL;
        new_record->next = hash_table.head;
        hash_table.head = new_record;
    }
    pthread_rwlock_unlock(&hash_table.lock);
}