int main() {
    HashTable<std::string, int> myHashTable(5);
    myHashTable.insert("one", 1);
    myHashTable.insert("two", 2);
    myHashTable.insert("three", 3);
    std::cout << "Value associated with 'two': " << myHashTable.get("two") << std::endl;
    myHashTable.remove("two");
    if (myHashTable.contains("two")) {
        std::cout << "Found key 'two' in the hash table." << std::endl;
    } else {
        std::cout << "Key 'two' not found in the hash table." << std::endl;
    }
    return 0;
}