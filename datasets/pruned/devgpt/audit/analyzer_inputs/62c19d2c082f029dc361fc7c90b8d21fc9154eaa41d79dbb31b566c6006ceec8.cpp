void scheduleTasks(std::vector<Task>& tasks) {
    std::sort(tasks.begin(), tasks.end(), sortByDeadline);
    std::vector<Task> scheduledTasks;
    int currentTime = 0;
    for (const Task& task : tasks) {
        currentTime += task.priority;
        if (currentTime <= task.deadline) {
            scheduledTasks.push_back(task);
        }
    }
    displayTasks(scheduledTasks);
}