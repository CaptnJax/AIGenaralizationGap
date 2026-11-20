int main() {
    MyClass obj1(10, "Hello");
    MyClass obj2(20, "World");
    std::cout << obj1.myInt << " " << obj1.myString << std::endl;
    std::cout << obj2.myInt << " " << obj2.myString << std::endl;
    return 0;
}