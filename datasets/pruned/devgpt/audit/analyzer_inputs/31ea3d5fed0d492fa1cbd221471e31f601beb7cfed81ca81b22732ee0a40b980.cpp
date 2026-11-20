void scheduleTasks(std::vector<Task>& tasks) {
    std::vector<Task> scheduledTasks;
    std::sort(tasks.begin(), tasks.end(), sortByDeadline);
    int currentTime = 0;
    for (const Task& task : tasks) {
        currentTime += task.priority;
        if (currentTime <= task.deadline) {
            scheduledTasks.push_back(task);
        }
    }
    std::cout << "Scheduled Tasks:\n";
    std::cout << "-------------------------------------------------------\n";
    for (const Task& task : scheduledTasks) {
        std::cout << "Name: " << task.name << " | Priority: " << task.priority << " | Deadline: " << task.deadline << "\n";
    }
    std::cout << "-------------------------------------------------------\n";
}