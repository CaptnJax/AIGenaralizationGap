void deleteLinkedList(Node* head) {
    while (head != nullptr) {
        Node* current = head;
        head = head->next;
        delete current;
    }
}