void destroy_token(Token token) {
    free(token.value);
}