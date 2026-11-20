int main() {
    Vector2D object1Velocity(1.0f, 1.0f);
    Vector2D object2Velocity(-1.0f, -1.0f);
    Vector2D collisionDirection(-1.0f, 0.0f);
    Vector2D collisionNormal = CalculateCollisionNormal(collisionDirection);
    Reflect(object1Velocity, collisionNormal);
    Reflect(object2Velocity, collisionNormal);
    std::cout << "New velocities:" << std::endl;
    std::cout << "Object 1: (" << object1Velocity.x << ", " << object1Velocity.y << ")" << std::endl;
    std::cout << "Object 2: (" << object2Velocity.x << ", " << object2Velocity.y << ")" << std::endl;
    return 0;
}