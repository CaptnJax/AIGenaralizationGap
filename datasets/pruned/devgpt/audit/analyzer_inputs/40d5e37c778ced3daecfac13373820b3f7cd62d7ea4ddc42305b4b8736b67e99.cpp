int main()
{
    std::cout << "Starting the program...\n";
    std::ifstream infile("grades");
    if (!infile) {
        std::cerr << "Could not open the file.\n";
        return 1;
    }
    std::cout << "Opened the grades file successfully.\n";
    std::string line;
    std::getline(infile, line);
    std::cout << "Allocating memory for student pointers...\n";
    student **student_ptrs = (student **)malloc(18 * sizeof(student *));
    std::cout << "Memory allocated successfully.\n";
    std::cout << "Reading and initializing student data...\n";
    std::string first, last;
    int exam1, exam2, exam3;
    for (int i = 0; i < 18; ++i) {
        infile >> first >> last >> exam1 >> exam2 >> exam3;
        std::cout << "Read data for student " << i+1 << ": " << first << " " << last << "\n";
        student_ptrs[i] = (student *)malloc(sizeof(student));
        student_ptrs[i]->first = strdup(first.c_str());
        student_ptrs[i]->last = strdup(last.c_str());
        student_ptrs[i]->exam1 = exam1;
        student_ptrs[i]->exam2 = exam2;
        student_ptrs[i]->exam3 = exam3;
        student_ptrs[i]->mean = (exam1 + exam2 + exam3) / 3.0;
    }
    std::cout << "Student data initialized successfully.\n";
    infile.close();
    std::cout << "Closed the grades file.\n";
    std::cout << "Sorting students by mean score...\n";
    bubble(student_ptrs, 18);
    std::cout << "Sorting complete.\n";
    std::cout << "Displaying sorted students:\n";
    for (int i = 0; i < 18; ++i) {
        std::cout << student_ptrs[i]->first << " " << student_ptrs[i]->last << " " << student_ptrs[i]->mean << std::endl;
        free(student_ptrs[i]->first);
        free(student_ptrs[i]->last);
        free(student_ptrs[i]);
    }
    std::cout << "Displayed all sorted students.\n";
    std::cout << "Freeing dynamically allocated memory...\n";
    free(student_ptrs);
    std::cout << "Memory freed successfully.\n";
    std::cout << "Program completed successfully.\n";
    return 0;
}