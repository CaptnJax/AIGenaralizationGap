int main() {
    std::ofstream svgFile("output.svg");
    if (!svgFile.is_open()) {
        std::cerr << "Error opening file!" << std::endl;
        return 1;
    }
    svgFile << "<svg width=\"100\" height=\"100\" xmlns=\"http://www.w3.org/2000/svg\">" << std::endl;
    svgFile << "<rect width=\"80\" height=\"80\" fill=\"blue\"/>" << std::endl;
    svgFile << "</svg>" << std::endl;
    svgFile.close();
    return 0;
}