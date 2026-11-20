bool shouldSwap(struct Record* rec1, struct Record* rec2) {
    int nameComparison = strcmp(rec1->name, rec2->name);
    if (nameComparison < 0) {
        return true;
    } else if (nameComparison == 0) {
        int surnameComparison = strcmp(rec1->surname, rec2->surname);
        if (surnameComparison < 0) {
            return true;
        }
    }
    return false;
}