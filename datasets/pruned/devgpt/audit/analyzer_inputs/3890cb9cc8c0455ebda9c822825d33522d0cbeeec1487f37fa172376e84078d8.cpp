int main(int argc, char** argv) {
    TaskScheduler* scheduler = BasicTaskScheduler::createNew();
    UsageEnvironment* env = BasicUsageEnvironment::createNew(*scheduler);
    RTSPServer* rtspServer = RTSPServer::createNew(*env, 554);
    ServerMediaSession* sms = ServerMediaSession::createNew(*env, "my_channel", nullptr, "My Channel Description");
    DeviceSource* deviceSource = DeviceSource::createNew(*env, "/dev/video0");
    H264VideoStreamDiscreteFramer* videoSource = H264VideoStreamDiscreteFramer::createNew(*env, deviceSource);
    sms->addSubsession(videoSource);
    rtspServer->addServerMediaSession(sms);
    env->taskScheduler().doEventLoop();
    delete rtspServer;
    delete scheduler;
    return 0;
}