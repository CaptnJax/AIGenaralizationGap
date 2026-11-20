void SVGWriter::writeCircle(double cx, double cy, double r, const std::string &strokeColor, const std::string &fillColor, double strokeWidth) {
    svgFile << "<circle cx=\"" << cx << "\" cy=\"" << cy << "\" r=\"" << r << "\" stroke=\"" << strokeColor << "\" fill=\"" << fillColor << "\" stroke-width=\"" << strokeWidth << "\" />" << std::endl;
}