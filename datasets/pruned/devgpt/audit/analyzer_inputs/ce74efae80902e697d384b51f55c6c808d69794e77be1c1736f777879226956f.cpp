int main() {
    std::function<int(int)> factorial;
    factorial = [&factorial](int n) -> int {
        if (n <= 1) return 1;
        else return n * factorial(n - 1);
    };
    std::cout << "Factorial of 5 is " << factorial(5) << std::endl;
    return 0;
}