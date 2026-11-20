void printDoublyLinkedList(BiNode* head) {
    while (head != nullptr) {
        std::cout << head->data << " ";
        head = head->node2;
    }
    std::cout << std::endl;
}