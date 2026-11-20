fixed_point_t exp_fixed_point(fixed_point_t x) {
  fixed_point_t result = 0;
  fixed_point_t term = 1 << FRACTIONAL_BITS;
  for (int n = 0; n < 10; ++n) {
    result += term;
    term = (term * x) / (n + 1) >> FRACTIONAL_BITS;
  }
  return result;
}