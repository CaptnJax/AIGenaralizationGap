void inorderTraversal(TreeNode* root) {
    if (root == nullptr) {
        return;
    }
    std::stack<TreeNode*> stack;
    while (root != nullptr || !stack.empty()) {
        while (root != nullptr) {
            stack.push(root);
            root = root->left;
        }
        root = stack.top();
        stack.pop();
        std::cout << root->data << " ";
        root = root->right;
    }
}