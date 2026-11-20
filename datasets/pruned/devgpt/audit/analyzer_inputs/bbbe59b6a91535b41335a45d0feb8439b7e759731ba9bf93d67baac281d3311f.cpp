int main() {
  std::string timestamp_str = "220517100000";
  std::tm timestamp_tm = {};
  std::stringstream ss(timestamp_str);
  ss >> std::get_time(&timestamp_tm, "%y%m%d%H%M%S");
  std::time_t timestamp_unix = std::mktime(&timestamp_tm);
  std::cout << "Unix timestamp: " << timestamp_unix << std::endl;
  return 0;
}