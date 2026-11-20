int main() {
    Vector2D object1Velocity(1.0f, 1.0f);
    Vector2D object2Velocity(-1.0f, -1.0f);
    Vector2D collisionDirection(-1.0f, 0.0f);
    if (collisionDirection.x < 0.0f) {
        Reflect(object1Velocity, Vector2D(-1.0f, 0.0f));
        Reflect(object2Velocity, Vector2D(-1.0f, 0.0f));
    } else if (collisionDirection.x > 0.0f) {
        Reflect(object1Velocity, Vector2D(1.0f, 0.0f));
        Reflect(object2Velocity, Vector2D(1.0f, 0.0f));
    } else if (collisionDirection.y < 0.0f) {
        Reflect(object1Velocity, Vector2D(0.0f, -1.0f));
        Reflect(object2Velocity, Vector2D(0.0f, -1.0f));
    } else if (collisionDirection.y > 0.0f) {
        Reflect(object1Velocity, Vector2D(0.0f, 1.0f));
        Reflect(object2Velocity, Vector2D(0.0f, 1.0f));
    }
    std::cout << "New velocities:" << std::endl;
    std::cout << "Object 1: (" << object1Velocity.x << ", " << object1Velocity.y << ")" << std::endl;
    std::cout << "Object 2: (" << object2Velocity.x << ", " << object2Velocity.y << ")" << std::endl;
    return 0;
}