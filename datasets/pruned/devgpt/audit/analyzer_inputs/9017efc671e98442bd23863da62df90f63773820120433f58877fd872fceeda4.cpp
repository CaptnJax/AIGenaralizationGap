int main() {
    BiNode* root = new BiNode(4);
    root->node1 = new BiNode(2);
    root->node2 = new BiNode(5);
    root->node1->node1 = new BiNode(1);
    root->node1->node2 = new BiNode(3);
    BiNode* head = BinaryTreeToDoublyLinkedList::convertBSTToDLL(root);
    std::cout << "Doubly Linked List: ";
    printDoublyLinkedList(head);
    delete root->node1->node1;
    delete root->node1->node2;
    delete root->node1;
    delete root->node2;
    delete root;
    return 0;
}