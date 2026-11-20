int main() {
    std::cout << "Size of Empty: " << sizeof(Empty) << '\n';
    std::cout << "Size of NotEmpty: " << sizeof(NotEmpty) << '\n';
    if(sizeof(Empty) == 1) {
        std::cout << "Empty struct has no non-static data members" << '\n';
    }
    if(sizeof(NotEmpty) == 1) {
        std::cout << "NotEmpty struct has no non-static data members" << '\n';
    }
    return 0;
}