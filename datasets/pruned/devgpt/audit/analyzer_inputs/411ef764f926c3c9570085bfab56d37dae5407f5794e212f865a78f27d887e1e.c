bool is_balanced(const char* expression) {
    Stack stack;
    initialize(&stack);
    const char* opening_symbols = "([{";
    const char* closing_symbols = ")]}";
    for (int i = 0; expression[i] != '\0'; i++) {
        char symbol = expression[i];
        if (strchr(opening_symbols, symbol) != NULL) {
            push(&stack, symbol);
        } else if (strchr(closing_symbols, symbol) != NULL) {
            if (is_empty(&stack)) {
                return false;
            }
            char opening_symbol = pop(&stack);
            const char* matching_opening_symbol = strchr(opening_symbols, opening_symbol);
            const char* matching_closing_symbol = strchr(closing_symbols, symbol);
            if (matching_opening_symbol - opening_symbols != matching_closing_symbol - closing_symbols) {
                return false;
            }
        }
    }
    return is_empty(&stack);
}