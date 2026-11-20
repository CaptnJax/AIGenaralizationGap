long long findPythagoreanProduct(int sumOfSides) {
    if (sumOfSides < 12)
        return -1;
    long long maxProduct = -1;
    for (int m = 2; m * m < sumOfSides; ++m) {
        for (int n = 1; n < m; ++n) {
            int a = m * m - n * n;
            int b = 2 * m * n;
            int c = m * m + n * n;
            if (a + b + c == sumOfSides && isPythagorean(a, b, c)) {
                long long product = a * b * c;
                maxProduct = std::max(maxProduct, product);
            }
        }
    }
    return maxProduct;
}