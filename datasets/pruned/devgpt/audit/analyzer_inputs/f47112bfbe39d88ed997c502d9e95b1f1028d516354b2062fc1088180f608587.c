static void skip_whitespace(Lexer* lexer) {
    while (isspace(peek_char(lexer))) {
        advance_char(lexer);
    }
}