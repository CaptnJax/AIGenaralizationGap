void SVGWriter::writeLine(double x1, double y1, double x2, double y2, const std::string &strokeColor, double strokeWidth, const std::string &markerStart) {
    svgFile << "<line x1=\"" << x1 << "\" y1=\"" << y1 << "\" x2=\"" << x2 << "\" y2=\"" << y2 << "\" stroke=\"" << strokeColor << "\" stroke-width=\"" << strokeWidth << "\" marker-start=\"url(#" << markerStart << ")\" />" << std::endl;
}