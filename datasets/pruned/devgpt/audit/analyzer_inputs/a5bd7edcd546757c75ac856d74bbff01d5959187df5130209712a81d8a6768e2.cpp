int main()
{
    student students[3];
    students[0] = {"Erica", "Sanders", 75, 89, 67, 77.0};
    students[1] = {"Kelley", "Cummings", 74, 70, 79, 74.3};
    students[2] = {"Jamie", "Reynolds", 64, 52, 66, 60.7};
    student* student_ptrs[3];
    for (int i = 0; i < 3; ++i) {
        student_ptrs[i] = &students[i];
    }
    bubble(student_ptrs, 3);
    for (int i = 0; i < 3; ++i) {
        std::cout << student_ptrs[i]->first << " " << student_ptrs[i]->last << " " << student_ptrs[i]->mean << std::endl;
    }
    return 0;
}