int main() {
    std::list<int> myList = {1, 2, 3, 4};
    myList.insert(myList.begin(), 0);
    std::list<int>::iterator it = std::next(myList.begin(), 2);
    myList.insert(it, 5);
    std::list<int> newElements = {6, 7, 8};
    myList.insert(it, newElements.begin(), newElements.end());
    for (int num : myList) {
        std::cout << num << " ";
    }
    std::cout << std::endl;
    return 0;
}