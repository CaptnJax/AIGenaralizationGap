int main(int argc, char** argv) {
    TaskScheduler* scheduler = BasicTaskScheduler::createNew();
    UsageEnvironment* env = BasicUsageEnvironment::createNew(*scheduler);
    RTSPClient* rtspClient = RTSPClient::createNew(*env, "rtsp://129.180.1.1:554/my_channel", 0, nullptr, 0);
    MediaSession* mediaSession = MediaSession::createNew(*env, "my_channel", "Stream from my_channel", "Session description");
    H264VideoRTPSink* videoSink = H264VideoRTPSink::createNew(*env, rtspClient->createNewStream(0), 96);
    mediaSession->addSubsession(videoSink);
    mediaSession->initiate();
    env->taskScheduler().doEventLoop();
    delete rtspClient;
    delete scheduler;
    return 0;
}