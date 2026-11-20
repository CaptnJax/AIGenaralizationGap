Vector2D CalculateCollisionNormal(const Vector2D& collisionDirection) {
    return Vector2D(-collisionDirection.y, collisionDirection.x);
}