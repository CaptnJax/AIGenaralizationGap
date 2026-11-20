int main() {
    ofstream svgFile("output.svg");
    if (!svgFile.is_open()) {
        cerr << "Error opening file!" << endl;
        return 1;
    }
    int svgWidth = 200;
    int svgHeight = 200;
    int rectWidth = 120;
    int rectHeight = 80;
    svgFile << "<svg width=\"" << svgWidth << "\" height=\"" << svgHeight << "\" xmlns=\"http://www.w3.org/2000/svg\">" << endl;
    svgFile << "<rect width=\"" << rectWidth << "\" height=\"" << rectHeight << "\" fill=\"blue\"/>" << endl;
    svgFile << "</svg>" << endl;
    svgFile.close();
    return 0;
}