int main() {
    struct Record record1 = {1, "John", "Doe", "123 Main St"};
    struct Record record2 = {2, "Alice", "Smith", "456 Oak St"};
    if (shouldSwap(&record1, &record2)) {
        printf("Swapping records.\n");
    } else {
        printf("No need to swap records.\n");
    }
    printf("Hello world.\n");
    return 0;
}