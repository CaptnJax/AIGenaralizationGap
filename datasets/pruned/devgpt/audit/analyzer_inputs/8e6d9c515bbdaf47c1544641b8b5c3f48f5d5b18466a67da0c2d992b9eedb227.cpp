int complex_operation(int x, int y) {
    int a = (x / 2) * y;
    a = a + (x % 3);
    int b = x;
    b = b + (y / 2);
    int c = x * y;
    c = c + (x / y);
    int intermediate_result = a * b;
    int result = intermediate_result / c;
    return result;
}