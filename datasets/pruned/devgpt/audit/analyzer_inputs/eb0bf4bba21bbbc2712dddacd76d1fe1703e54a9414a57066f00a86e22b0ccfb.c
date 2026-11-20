void insert(const char *name, int salary) {
    uint32_t hash = jenkins_one_at_a_time_hash((const uint8_t *)name, strlen(name));
    pthread_mutex_lock(&hash_table.lock);
    hashRecord *current = hash_table.head;
    hashRecord *prev = NULL;
    while (current != NULL) {
        if (current->hash == hash && strcmp(current->name, name) == 0) {
            current->salary = salary;
            pthread_mutex_unlock(&hash_table.lock);
            return;
        }
        prev = current;
        current = current->next;
    }
    hashRecord *new_record = (hashRecord *)malloc(sizeof(hashRecord));
    new_record->hash = hash;
    strncpy(new_record->name, name, 50);
    new_record->name[49] = '\0';
    new_record->salary = salary;
    new_record->next = NULL;
    if (prev == NULL) {
        hash_table.head = new_record;
    } else {
        prev->next = new_record;
    }
    pthread_mutex_unlock(&hash_table.lock);
}