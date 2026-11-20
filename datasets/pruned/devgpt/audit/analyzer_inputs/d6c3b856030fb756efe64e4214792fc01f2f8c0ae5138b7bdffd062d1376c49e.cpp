void Normalize(Vector2D& vector) {
    float length = std::sqrt(vector.x * vector.x + vector.y * vector.y);
    vector.x /= length;
    vector.y /= length;
}