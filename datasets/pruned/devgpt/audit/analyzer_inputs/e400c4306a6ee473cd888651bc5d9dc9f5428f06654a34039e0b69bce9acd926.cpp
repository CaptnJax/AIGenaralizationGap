int main() {
    cPlayer player("John");
    cStreet street;
    cHouse house;
    cComputer computer;
    cBook book;
    player.buy(street, "Street");
    player.buy(house, "House");
    player.buy(computer, "Computer");
    player.buy(book, "Book");
    return 0;
}