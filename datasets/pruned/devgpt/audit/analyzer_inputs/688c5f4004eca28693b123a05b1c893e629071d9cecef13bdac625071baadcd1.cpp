void setup() {
  Serial.begin(9600);
  fixed_point_t x = 1 << FRACTIONAL_BITS;
  fixed_point_t result = exp_fixed_point(x);
  Serial.print("exp(1) in fixed-point representation: ");
  Serial.println(result);
}