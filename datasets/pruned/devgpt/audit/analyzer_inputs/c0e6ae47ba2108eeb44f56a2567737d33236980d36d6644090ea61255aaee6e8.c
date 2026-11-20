Parser* create_parser(const char* source) {
    Parser* parser = (Parser*)malloc(sizeof(Parser));
    parser->lexer = create_lexer(source);
    parser->current_token = next_token(parser->lexer);
    return parser;
}