int main() {
  std::string timestamp_str = "231031020000";
  std::tm timestamp_tm = {};
  std::stringstream ss(timestamp_str);
  ss >> std::get_time(&timestamp_tm, "%y%m%d%H%M%S");
  timestamp_tm.tm_isdst = -1;
  std::time_t timestamp_unix = std::mktime(&timestamp_tm);
  std::cout << "Unix timestamp: " << timestamp_unix << std::endl;
  std::cout << "DST flag: " << timestamp_tm.tm_isdst << std::endl;
  return 0;
}