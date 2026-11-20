CGEventRef tapCallback(CGEventTapProxy proxy, CGEventType type, CGEventRef event, void* refcon) {
    double now = CFAbsoluteTimeGetCurrent();
    if (type == kCGEventRightMouseDown) {
        rightClickDown = now;
    } else if (type == kCGEventRightMouseUp) {
        if (now - rightClickDown >= 1.0) {
            exit(0);
        }
    }
    return nullptr;
}