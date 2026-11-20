void writeMarker(std::ofstream &svgFile, const std::string &markerId) {
    svgFile << "<defs>" << std::endl;
    svgFile << "  <marker style=\"overflow:visible\" id=\"" << markerId << "\" refX=\"0.0\" refY=\"0.0\" orient=\"auto\">" << std::endl;
    svgFile << "    <path transform=\"scale(0.2) translate(6,0)\" style=\"fill-rule:evenodd;fill:context-stroke;stroke:context-stroke;stroke-width:1.0pt\" d=\"M 0.0,0.0 L 5.0,-5.0 L -12.5,0.0 L 5.0,5.0 L 0.0,0.0 z \" />" << std::endl;
    svgFile << "  </marker>" << std::endl;
    svgFile << "</defs>" << std::endl;
}