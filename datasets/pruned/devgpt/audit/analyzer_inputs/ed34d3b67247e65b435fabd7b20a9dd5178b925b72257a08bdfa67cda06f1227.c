static Token scan_number(Lexer* lexer) {
    size_t start = lexer->position - 1;
    while (isdigit(peek_char(lexer))) {
        advance_char(lexer);
    }
    char* value = strndup(lexer->source + start, lexer->position - start);
    return make_token(TOKEN_INT, value);
}