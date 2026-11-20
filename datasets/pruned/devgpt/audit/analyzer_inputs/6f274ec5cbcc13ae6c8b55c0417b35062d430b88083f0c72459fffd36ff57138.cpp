int main()
{
    std::ifstream infile("grades");
    if (!infile) {
        std::cerr << "Could not open the file." << std::endl;
        return 1;
    }
    std::string line;
    std::getline(infile, line);
    student **student_ptrs = (student **)malloc(18 * sizeof(student *));
    std::string first, last;
    int exam1, exam2, exam3;
    for (int i = 0; i < 18; ++i) {
        infile >> first >> last >> exam1 >> exam2 >> exam3;
        student_ptrs[i] = (student *)malloc(sizeof(student));
        student_ptrs[i]->first = strdup(first.c_str());
        student_ptrs[i]->last = strdup(last.c_str());
        student_ptrs[i]->exam1 = exam1;
        student_ptrs[i]->exam2 = exam2;
        student_ptrs[i]->exam3 = exam3;
        student_ptrs[i]->mean = (exam1 + exam2 + exam3) / 3.0;
    }
    infile.close();
    bubble(student_ptrs, 18);
    for (int i = 0; i < 18; ++i) {
        std::cout << student_ptrs[i]->first << " " << student_ptrs[i]->last << " " << student_ptrs[i]->mean << std::endl;
        free(student_ptrs[i]->first);
        free(student_ptrs[i]->last);
        free(student_ptrs[i]);
    }
    free(student_ptrs);
    return 0;
}