int main() {
    printf("%d\n", is_balanced("()"));
    printf("%d\n", is_balanced("({[]})"));
    printf("%d\n", is_balanced("({)}"));
    printf("%d\n", is_balanced("[[[]]]"));
    printf("%d\n", is_balanced("(]"));
    return 0;
}