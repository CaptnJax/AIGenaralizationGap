void Reflect(Vector2D& velocity, const Vector2D& collisionNormal) {
    float dotProduct = velocity.x * collisionNormal.x + velocity.y * collisionNormal.y;
    velocity.x = velocity.x - 2.0f * dotProduct * collisionNormal.x;
    velocity.y = velocity.y - 2.0f * dotProduct * collisionNormal.y;
}