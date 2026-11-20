void TestS4x27(void)
{
  SFixed<4, 27> a = -9.1233459;
  SFixed<4, 27> result = exp_fixed_point(a);
  Serial.println(static_cast<float>(result), 7);
}