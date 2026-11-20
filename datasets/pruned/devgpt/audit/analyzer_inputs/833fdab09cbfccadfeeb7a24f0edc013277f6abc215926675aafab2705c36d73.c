char pop(Stack* stack) {
    if (is_empty(stack)) {
        printf("Stack underflow!\n");
        exit(1);
    }
    return stack->stack[stack->top--];
}