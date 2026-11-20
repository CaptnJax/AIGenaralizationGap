int main() {
    CFMachPortRef eventTap;
    CGEventMask mask = kCGEventMaskForAllEvents;
    eventTap = CGEventTapCreate(kCGHIDEventTap, kCGHeadInsertEventTap,
        kCGEventTapOptionDefault, mask, tapCallback, nullptr);
    if (!eventTap) {
        std::cerr << "Failed to create event tap." << std::endl;
        return 1;
    }
    CFRunLoopSourceRef runLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, eventTap, 0);
    CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, kCFRunLoopCommonModes);
    CGEventTapEnable(eventTap, true);
    CFRunLoopRun();
    CFRelease(runLoopSource);
    CFRelease(eventTap);
    return 0;
}