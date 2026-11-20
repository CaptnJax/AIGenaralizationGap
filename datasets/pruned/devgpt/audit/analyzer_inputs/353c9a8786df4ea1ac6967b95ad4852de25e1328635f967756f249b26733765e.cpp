void closeSVGFile(std::ofstream &svgFile) {
    svgFile << "</svg>" << std::endl;
    svgFile.close();
}