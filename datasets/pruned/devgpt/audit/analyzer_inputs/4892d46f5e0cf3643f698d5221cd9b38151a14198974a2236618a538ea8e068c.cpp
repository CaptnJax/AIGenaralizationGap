string convertThreeDigits(int num) {
    string ones[] = {"", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"};
    string teens[] = {"", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"};
    string tens[] = {"", "Ten", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"};
    string result;
    int hundred = num / 100;
    int ten = (num % 100) / 10;
    int one = num % 10;
    if (hundred > 0) {
        result += ones[hundred] + " Hundred ";
    }
    if (ten == 1) {
        result += teens[one] + " ";
    } else {
        if (ten > 1) {
            result += tens[ten] + " ";
        }
        if (one > 0) {
            result += ones[one] + " ";
        }
    }
    return result;
}