static Token scan_identifier(Lexer* lexer) {
    size_t start = lexer->position - 1;
    while (isalnum(peek_char(lexer)) || peek_char(lexer) == '_') {
        advance_char(lexer);
    }
    char* value = strndup(lexer->source + start, lexer->position - start);
    return make_token(TOKEN_IDENTIFIER, value);
}