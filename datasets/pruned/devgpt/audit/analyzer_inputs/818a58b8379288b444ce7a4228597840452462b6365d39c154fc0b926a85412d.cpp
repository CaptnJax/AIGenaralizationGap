void workerFunction()
{
    proj_context* projCtx;
    {
        std::lock_guard<std::mutex> lock(projMutex);
        projCtx = proj_context_create();
    }
    CPLSetThreadLocalConfigOption("OGR_ENABLE_PARTIAL_REPROJECTION", "YES");
    CPLSetThreadLocalConfigOption("OGR_ENABLE_PARTIAL_REPROJECTION_THREADS", "YES");
    CPLSetThreadLocalConfigOption("PROJ_THREAD_SAFE", "YES");
    OGRRegisterAll();
    OGRSpatialReference sourceSRS;
    OGRSpatialReference targetSRS;
    sourceSRS.importFromEPSG(4326);
    targetSRS.importFromEPSG(3857);
    OGRCoordinateTransformation* transformation = OGRCreateCoordinateTransformation(&sourceSRS, &targetSRS);
    OGRCoordinateTransformation::DestroyCT(transformation);
    {
        std::lock_guard<std::mutex> lock(projMutex);
        proj_context_destroy(projCtx);
    }
}