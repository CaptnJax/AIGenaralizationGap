DerivedClass::DerivedClass(int derivedValue, int baseValue) : BaseClass(baseValue) {
    std::cout << "DerivedClass constructor called. DerivedValue: " << derivedValue << std::endl;
}