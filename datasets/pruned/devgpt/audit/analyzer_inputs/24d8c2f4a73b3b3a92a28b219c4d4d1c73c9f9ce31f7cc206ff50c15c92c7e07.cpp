void setup_logger() {
    auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
    auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>("my_app.log", true);
    auto hello_imgui_sink = std::make_shared<hello_imgui_sink_mt>();
    spdlog::logger logger("multi_sink", {console_sink, file_sink, hello_imgui_sink});
    logger.set_level(spdlog::level::debug);
    spdlog::set_default_logger(std::make_shared<spdlog::logger>(logger));
}