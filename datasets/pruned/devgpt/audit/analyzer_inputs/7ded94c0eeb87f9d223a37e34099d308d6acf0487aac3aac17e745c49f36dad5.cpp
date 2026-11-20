int main() {
    int number;
    std::cout << "Enter a number: ";
    std::cin >> number;
    if (number < 0) {
        std::cout << "Factorial is not defined for negative numbers." << std::endl;
    } else {
        std::cout << "Factorial of " << number << " is " << factorial(number) << std::endl;
    }
    return 0;
}