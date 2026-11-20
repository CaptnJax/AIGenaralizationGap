std::string findMonth(int index) {
    const int startingIndices[] = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
    const char* monthNames[] = {"JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"};
    for (int i = 0; i < 12; ++i) {
        if (index >= startingIndices[i] && index < startingIndices[i + 1]) {
            return monthNames[i];
        }
    }
    return "";
}