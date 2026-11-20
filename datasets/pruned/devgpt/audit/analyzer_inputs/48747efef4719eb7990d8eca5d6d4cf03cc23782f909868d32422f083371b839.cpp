std::optional<double> safe_reciprocal(double x) {
    if(x != 0)
        return 1 / x;
    else
        return std::nullopt;
}