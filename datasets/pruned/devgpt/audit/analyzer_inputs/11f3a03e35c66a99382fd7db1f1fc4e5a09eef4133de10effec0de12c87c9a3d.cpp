template<typename Iterator>
Iterator find_begin(Iterator begin, Iterator end) {
    while (begin != end && std::isspace(*begin)) {
        ++begin;
    }
    return begin;
}