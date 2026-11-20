int main() {
    std::string text = "   Hello, world!   ";
    auto begin = find_begin(text.begin(), text.end());
    auto end = find_end(text.begin(), text.end());
    std::string stripped_text(begin, end);
    std::cout << "Stripped text: '" << stripped_text << "'" << std::endl;
    return 0;
}