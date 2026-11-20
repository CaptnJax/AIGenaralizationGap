int main() {
    MyClass obj1(42);
    MyClass obj2(0);
    obj2.assignObject(obj1);
    obj2.printData();
    MyClass obj3(0);
    obj3.assignObject(std::move(obj1));
    obj3.printData();
    return 0;
}