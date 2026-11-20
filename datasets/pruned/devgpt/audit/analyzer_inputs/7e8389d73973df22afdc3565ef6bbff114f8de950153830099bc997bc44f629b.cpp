int complex_operation(int x, int y) {
    int a = (x / 2) * y + (x % 3);
    int b = x + (y / 2);
    int c = (x * y) + (x / y);
    int result = (a * b) / c;
    return result;
}