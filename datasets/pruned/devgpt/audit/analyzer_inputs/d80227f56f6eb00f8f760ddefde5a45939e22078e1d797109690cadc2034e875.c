Token next_token(Lexer* lexer) {
    skip_whitespace(lexer);
    char current = advance_char(lexer);
    if (isdigit(current)) {
        return scan_number(lexer);
    }
    if (isalpha(current) || current == '_') {
        return scan_identifier(lexer);
    }
    switch (current) {
        case '\0': return make_token(TOKEN_EOF, "");
        case '(': return make_token(TOKEN_LPAREN, "(");
        case ')': return make_token(TOKEN_RPAREN, ")");
        case ':': return make_token(TOKEN_COLON, ":");
        case ',': return make_token(TOKEN_COMMA, ",");
        case '-':
            if (peek_char(lexer) == '>') {
                advance_char(lexer);
                return make_token(TOKEN_RANGE, "->");
            }
            break;
    }
    char unknown[2] = { current, '\0' };
    return make_token(TOKEN_UNKNOWN, unknown);
}