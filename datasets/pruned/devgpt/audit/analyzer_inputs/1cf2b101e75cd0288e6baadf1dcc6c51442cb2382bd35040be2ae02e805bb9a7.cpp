int main() {
    std::vector<Task> tasks;
    while (true) {
        std::cout << "1. Add Task\n";
        std::cout << "2. Schedule Tasks\n";
        std::cout << "3. Exit\n";
        int choice;
        std::cin >> choice;
        if (choice == 1) {
            std::string name;
            int priority, deadline;
            std::cout << "Enter Task Name: ";
            std::cin >> name;
            std::cout << "Enter Task Priority: ";
            std::cin >> priority;
            std::cout << "Enter Task Deadline: ";
            std::cin >> deadline;
            tasks.emplace_back(name, priority, deadline);
        } else if (choice == 2) {
            scheduleTasks(tasks);
        } else if (choice == 3) {
            break;
        } else {
            std::cout << "Invalid choice. Please try again.\n";
        }
    }
    return 0;
}