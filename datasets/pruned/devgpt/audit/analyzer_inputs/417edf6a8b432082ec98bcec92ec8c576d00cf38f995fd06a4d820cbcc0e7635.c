void* hash_table_thread_function(void* arg) {
    thread_args_t* args = (thread_args_t*)arg;
    char buffer[BUFFER_SIZE];
    line_t line;
    pthread_mutex_lock(&file_mutex);
    fgets(buffer, BUFFER_SIZE, args->in_fp);
    line = parse_line(buffer);
    pthread_mutex_unlock(&file_mutex);
    if( !strcmp(line.command, "insert") ) {
        insert(args->hash_table, HASH_TABLE_SIZE, args->lock, line.param_one, atoi(line.param_two), args->out_fp);
    }
    else if( !strcmp(line.command, "delete") ) {
    }
    else if( !strcmp(line.command, "search") ) {
    }
    else if( !strcmp(line.command, "print") ) {
        print(args->hash_table, HASH_TABLE_SIZE, args->lock, args->out_fp);
    }
    free_line(line);
    return NULL;
}