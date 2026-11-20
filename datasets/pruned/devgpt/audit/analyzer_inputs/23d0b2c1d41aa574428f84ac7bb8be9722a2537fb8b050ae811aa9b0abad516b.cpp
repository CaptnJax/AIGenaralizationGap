std::vector<std::string> binTree::zigzagRight(binTreeNode* r, std::vector<std::string>& path)
{
    if (r == nullptr)
        return std::vector<std::string>();
    path.push_back(r->location);
    std::vector<std::string> leftPath = zigzagRight(r->left, std::vector<std::string>());
    std::vector<std::string> rightPath = zigzagRight(r->right, path);
    return (leftPath.size() > rightPath.size()) ? leftPath : rightPath;
}