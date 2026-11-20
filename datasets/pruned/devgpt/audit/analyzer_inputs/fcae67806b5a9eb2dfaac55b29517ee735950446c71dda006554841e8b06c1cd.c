void print_record(const hashRecord *record) {
    printf("%u,%s,%u\n", record->hash, record->name, record->salary);
}