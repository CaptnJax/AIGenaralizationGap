int main() {
    std::string str = "   Hello, world!   ";
    auto begin = find_begin(str.begin(), str.end());
    auto end = find_end(str.begin(), str.end());
    for (auto it = begin; it != end; ++it) {
        std::cout << *it;
    }
    std::cout << std::endl;
    return 0;
}