void updateActivity(double elapsedTime) {
    const double epsilon = 1e-5;
    if (std::abs(elapsedTime - lastCastTime) >= durationSeconds - epsilon) {
        isActive = false;
    }
}