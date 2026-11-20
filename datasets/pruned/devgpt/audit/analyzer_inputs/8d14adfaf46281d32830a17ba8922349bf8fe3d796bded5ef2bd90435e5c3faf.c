char** hash_table_to_env_array(t_env_table* ht) {
    char** env_array = malloc((ht->count + 1) * sizeof(char*));
    if (!env_array) {
        return NULL;
    }
    int index = 0;
    for (int i = 0; i < TABLE_SIZE; i++) {
        t_env_var* node = ht->table[i];
        while (node != NULL) {
            env_array[index] = str_join_with_separator(node->key, "=", node->value);
            index++;
            node = node->next;
        }
    }
    env_array[ht->count] = NULL;
    return env_array;
}