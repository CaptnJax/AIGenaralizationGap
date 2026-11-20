template <int Integer, int Fraction>
SFixed<Integer, Fraction> exp_fixed_point(const SFixed<Integer, Fraction>& x) {
  SFixed<Integer, Fraction> result = 1;
  SFixed<Integer, Fraction> term = 1;
  for (int n = 1; n < 10; ++n) {
    term = (term * x) / factorial(n);
    result += term;
  }
  return result;
}