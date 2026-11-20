int main() {
    std::ofstream svgFile("output.svg");
    if (!svgFile.is_open()) {
        std::cerr << "Error opening file!" << std::endl;
        return 1;
    }
    int svgWidth = 200;
    int svgHeight = 200;
    int rectWidth = 120;
    int rectHeight = 80;
    svgFile << "<svg width=\"" << svgWidth << "\" height=\"" << svgHeight << "\" xmlns=\"http://www.w3.org/2000/svg\">" << std::endl;
    svgFile << "<rect width=\"" << rectWidth << "\" height=\"" << rectHeight << "\" fill=\"blue\"/>" << std::endl;
    svgFile << "</svg>" << std::endl;
    svgFile.close();
    return 0;
}