void writeRect(std::ofstream &svgFile, int width, int height, const std::string &fillColor) {
    svgFile << "<rect width=\"" << width << "\" height=\"" << height << "\" fill=\"" << fillColor << "\"/>" << std::endl;
}