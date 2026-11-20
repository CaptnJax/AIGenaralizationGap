SVGWriter::~SVGWriter() {
    svgFile << "</svg>" << std::endl;
    svgFile.close();
}