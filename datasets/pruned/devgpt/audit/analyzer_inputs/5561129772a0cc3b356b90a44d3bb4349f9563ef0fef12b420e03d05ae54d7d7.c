static void consume_token(Parser* parser, TokenType expected) {
    if (parser->current_token.type == expected) {
        destroy_token(parser->current_token);
        parser->current_token = next_token(parser->lexer);
    } else {
        fprintf(stderr, "Error: Expected token of type %d but got %d\n", expected, parser->current_token.type);
        exit(1);
    }
}