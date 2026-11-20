std::vector<std::string> binTree::zigzagLeft(binTreeNode* r, std::vector<std::string>& path)
{
    if (r == nullptr)
        return std::vector<std::string>();
    path.push_back(r->location);
    std::vector<std::string> leftPath = zigzagLeft(r->left, path);
    std::vector<std::string> rightPath = zigzagLeft(r->right, std::vector<std::string>());
    return (leftPath.size() > rightPath.size()) ? leftPath : rightPath;
}