template<typename Iterator>
Iterator find_end(Iterator begin, Iterator end) {
    return std::find_if_not(std::make_reverse_iterator(end), std::make_reverse_iterator(begin), [](char c) { return std::isspace(c); }).base();
}