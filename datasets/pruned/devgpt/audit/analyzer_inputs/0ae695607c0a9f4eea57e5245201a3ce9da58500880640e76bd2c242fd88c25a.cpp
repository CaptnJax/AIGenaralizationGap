int main() {
    Element family("family");
    family.attributes.emplace_back("lastName", "McDowel");
    family.attributes.emplace_back("state", "CA");
    Element person("person");
    person.attributes.emplace_back("firstName", "Gayle");
    person.value = "Some Message";
    family.children.push_back(person);
    std::string encodedXML = family.encode();
    std::cout << "Encoded XML: " << encodedXML << std::endl;
    return 0;
}