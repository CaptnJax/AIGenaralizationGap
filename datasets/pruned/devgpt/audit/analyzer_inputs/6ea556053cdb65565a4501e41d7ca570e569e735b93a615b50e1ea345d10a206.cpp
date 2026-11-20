template<typename Iterator>
Iterator find_end(Iterator begin, Iterator end) {
    while (begin != end && std::isspace(*(end - 1))) {
        --end;
    }
    return end;
}