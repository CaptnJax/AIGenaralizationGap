ConstrainedIntType* parse_constrained_int_type(Parser* parser) {
    ConstrainedIntType* result = (ConstrainedIntType*)malloc(sizeof(ConstrainedIntType));
    if (parser->current_token.type != TOKEN_IDENTIFIER) {
        fprintf(stderr, "Error: Expected identifier for type name\n");
        exit(1);
    }
    result->name = strdup(parser->current_token.value);
    consume_token(parser, TOKEN_IDENTIFIER);
    consume_token(parser, TOKEN_LPAREN);
    result->min_value = parse_integer(parser);
    consume_token(parser, TOKEN_RANGE);
    result->max_value = parse_integer(parser);
    consume_token(parser, TOKEN_RPAREN);
    return result;
}