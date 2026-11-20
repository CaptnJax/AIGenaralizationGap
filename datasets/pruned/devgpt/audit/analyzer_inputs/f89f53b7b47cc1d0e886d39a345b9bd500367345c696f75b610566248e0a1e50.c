void destroy_parser(Parser* parser) {
    destroy_token(parser->current_token);
    destroy_lexer(parser->lexer);
    free(parser);
}