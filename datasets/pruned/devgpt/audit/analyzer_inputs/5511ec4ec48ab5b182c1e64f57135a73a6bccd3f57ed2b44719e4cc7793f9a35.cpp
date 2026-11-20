void displayTasks(const std::vector<Task>& tasks) {
    std::cout << "Task List:\n";
    std::cout << "-------------------------------------------------------\n";
    for (const Task& task : tasks) {
        std::cout << "Name: " << task.name << " | Priority: " << task.priority << " | Deadline: " << task.deadline << "\n";
    }
    std::cout << "-------------------------------------------------------\n";
}