int main() {
    int q;
    std::cout << "How many times should this program be repeated: ";
    std::cin >> q;
    for (int i = 0; i < q; ++i) {
        int sumOfSides;
        std::cout << "Enter the sum of sides: ";
        std::cin >> sumOfSides;
        long long product = findPythagoreanProduct(sumOfSides);
        std::cout << "Product of Pythagorean triplet: " << product << std::endl;
    }
    return 0;
}