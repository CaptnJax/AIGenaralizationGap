int main(int argc, char** argv) {
    TaskScheduler* scheduler = BasicTaskScheduler::createNew();
    UsageEnvironment* env = BasicUsageEnvironment::createNew(*scheduler);
    RTSPServer* rtspServer = RTSPServer::createNew(*env, 8554);
    ServerMediaSession* sms = ServerMediaSession::createNew(*env, "StreamSession", nullptr, "Session description");
    H264VideoFileServerMediaSubsession* videoSubsession = H264VideoFileServerMediaSubsession::createNew(*env, "path_to_video_file");
    sms->addSubsession(videoSubsession);
    rtspServer->addServerMediaSession(sms);
    rtspServer->setUpTunnelingOverHTTP(80);
    env->taskScheduler().doEventLoop();
    delete rtspServer;
    delete scheduler;
    return 0;
}