void insert(const char *name, int salary) {
    pthread_mutex_lock(&hash_table.lock);
    hashRecord *current = hash_table.head;
    hashRecord *prev = NULL;
    while (current != NULL) {
        if (strcmp(current->name, name) == 0) {
            current->salary = salary;
            pthread_mutex_unlock(&hash_table.lock);
            return;
        }
        prev = current;
        current = current->next;
    }
    hashRecord *new_record = (hashRecord *)malloc(sizeof(hashRecord));
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