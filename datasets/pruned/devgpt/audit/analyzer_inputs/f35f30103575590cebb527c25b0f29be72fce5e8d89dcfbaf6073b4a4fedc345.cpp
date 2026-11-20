std::vector<std::string> binTree::zigzag()
{
    std::vector<std::string> vector1;
    std::vector<std::string> leftZag = zigzagLeft(root, vector1);
    std::vector<std::string> rightZag = zigzagRight(root, vector1);
    if (leftZag.size() + rightZag.size() == 0)
        return vector1;
    return (leftZag.size() > rightZag.size()) ? leftZag : rightZag;
}