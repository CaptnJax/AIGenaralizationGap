static int parse_integer(Parser* parser) {
    int value = atoi(parser->current_token.value);
    consume_token(parser, TOKEN_INT);
    return value;
}