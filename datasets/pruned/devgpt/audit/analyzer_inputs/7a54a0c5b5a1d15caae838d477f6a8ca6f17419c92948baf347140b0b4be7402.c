int main(void) {
    FILE* in_fp = open_input_file();
    FILE* out_fp = open_output_file();
    hash_record_t** hash_table = create_hash_table(HASH_TABLE_SIZE);
    char buffer[BUFFER_SIZE];
    fgets(buffer, BUFFER_SIZE, in_fp);
    line_t line = parse_line(buffer);
    uint32_t num_threads = atoi(line.param_one);
    free_line(line);
    fprintf(out_fp, "Running %d threads\n", num_threads);
    rwlock_t* lock = rwlock_init();
    thread_args_t thread_args = {.hash_table = hash_table, .in_fp = in_fp, .out_fp = out_fp, .lock = lock};
    pthread_t* threads = allocate_threads(num_threads);
    for(uint32_t i = 0; i < num_threads; i++) {
        pthread_create(&threads[i], NULL, hash_table_thread_function, (void*)&thread_args);
    }
    for(uint32_t i = 0; i < num_threads; i++) {
        pthread_join(threads[i] ,NULL);
    }
    fclose(in_fp);
    fclose(out_fp);
    free(lock);
    free(threads);
    free_hash_table(hash_table, HASH_TABLE_SIZE);
    return 0;
}