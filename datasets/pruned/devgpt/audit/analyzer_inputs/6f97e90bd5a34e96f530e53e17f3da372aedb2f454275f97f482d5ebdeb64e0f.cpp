bool AreFRectsEqual(const SDL_FRect& rect1, const SDL_FRect& rect2) {
    return (std::abs(rect1.x - rect2.x) < FLOAT_EPSILON) &&
           (std::abs(rect1.y - rect2.y) < FLOAT_EPSILON) &&
           (std::abs(rect1.w - rect2.w) < FLOAT_EPSILON) &&
           (std::abs(rect1.h - rect2.h) < FLOAT_EPSILON);
}