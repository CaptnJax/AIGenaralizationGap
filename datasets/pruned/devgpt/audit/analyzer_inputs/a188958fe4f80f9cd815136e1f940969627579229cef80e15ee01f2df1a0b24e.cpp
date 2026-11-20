std::optional<double> safe_square_root(double x) {
    if(x >= 0)
        return sqrt(x);
    else
        return std::nullopt;
}