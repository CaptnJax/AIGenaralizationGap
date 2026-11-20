int main()
{
    student **student_ptrs = (student **)malloc(3 * sizeof(student *));
    for (int i = 0; i < 3; ++i) {
        student_ptrs[i] = (student *)malloc(sizeof(student));
    }
    student_ptrs[0]->first = "Erica";
    student_ptrs[0]->last = "Sanders";
    student_ptrs[0]->exam1 = 75;
    student_ptrs[0]->exam2 = 89;
    student_ptrs[0]->exam3 = 67;
    student_ptrs[0]->mean = 77.0;
    student_ptrs[1]->first = "Kelley";
    student_ptrs[1]->last = "Cummings";
    student_ptrs[1]->exam1 = 74;
    student_ptrs[1]->exam2 = 70;
    student_ptrs[1]->exam3 = 79;
    student_ptrs[1]->mean = 74.3;
    student_ptrs[2]->first = "Jamie";
    student_ptrs[2]->last = "Reynolds";
    student_ptrs[2]->exam1 = 64;
    student_ptrs[2]->exam2 = 52;
    student_ptrs[2]->exam3 = 66;
    student_ptrs[2]->mean = 60.7;
    bubble(student_ptrs, 3);
    for (int i = 0; i < 3; ++i) {
        std::cout << student_ptrs[i]->first << " " << student_ptrs[i]->last << " " << student_ptrs[i]->mean << std::endl;
    }
    for (int i = 0; i < 3; ++i) {
        free(student_ptrs[i]);
    }
    free(student_ptrs);
    return 0;
}