void push(Stack* stack, char symbol) {
    if (is_full(stack)) {
        printf("Stack overflow!\n");
        exit(1);
    }
    stack->stack[++stack->top] = symbol;
}