uint32_t hash_function(const char *key) {
    uint32_t hash = 0;
    size_t i;
    for (i = 0; key[i] != '\0'; ++i) {
        hash += key[i];
        hash += (hash << 10);
        hash ^= (hash >> 6);
    }
    hash += (hash << 3);
    hash ^= (hash >> 11);
    hash += (hash << 15);
    return hash;
}