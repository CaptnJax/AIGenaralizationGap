void test() {
    PartialFunction<double, double> composed_function = compose(safe_reciprocal, safe_square_root);
    std::optional<double> res1 = composed_function(4);
    if(res1.has_value())
        std::cout << "Square root of the reciprocal of 4: " << res1.value() << std::endl;
    else
        std::cout << "Square root of the reciprocal of 4 is not defined" << std::endl;
    std::optional<double> res2 = composed_function(-4);
    if(res2.has_value())
        std::cout << "Square root of the reciprocal of -4: " << res2.value() << std::endl;
    else
        std::cout << "Square root of the reciprocal of -4 is not defined" << std::endl;
    std::optional<double> res3 = composed_function(0);
    if(res3.has_value())
        std::cout << "Square root of the reciprocal of 0: " << res3.value() << std::endl;
    else
        std::cout << "Square root of the reciprocal of 0 is not defined" << std::endl;
}