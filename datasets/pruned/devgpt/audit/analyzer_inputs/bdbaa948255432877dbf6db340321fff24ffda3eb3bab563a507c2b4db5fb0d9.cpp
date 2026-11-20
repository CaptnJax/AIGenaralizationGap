void openSVGFile(std::ofstream &svgFile, const std::string &filename, int width, int height) {
    svgFile.open(filename);
    if (!svgFile.is_open()) {
        std::cerr << "Error opening file!" << std::endl;
        exit(1);
    }
    svgFile << "<svg width=\"" << width << "\" height=\"" << height << "\" xmlns=\"http://www.w3.org/2000/svg\">" << std::endl;
}