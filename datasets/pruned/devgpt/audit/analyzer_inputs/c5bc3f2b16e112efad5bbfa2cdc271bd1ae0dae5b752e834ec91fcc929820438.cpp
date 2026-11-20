static void convertBSTToDLLHelper(BiNode* root, BiNode*& head, BiNode*& prev) {
    if (root == nullptr) {
        return;
    }
    convertBSTToDLLHelper(root->node1, head, prev);
    if (prev == nullptr) {
        head = root;
    } else {
        prev->node2 = root;
        root->node1 = prev;
    }
    prev = root;
    convertBSTToDLLHelper(root->node2, head, prev);
}