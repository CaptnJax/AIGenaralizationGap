template<typename Iterator>
Iterator find_begin(Iterator begin, Iterator end) {
    return std::find_if_not(begin, end, [](char c) { return std::isspace(c); });
}