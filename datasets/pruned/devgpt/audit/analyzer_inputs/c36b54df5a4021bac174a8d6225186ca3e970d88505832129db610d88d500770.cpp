int main() {
  std::string timestamp_str = "231031020000S";
  std::tm timestamp_tm = {};
  std::stringstream ss(timestamp_str.substr(0,14));
  ss >> std::get_time(&timestamp_tm, "%y%m%d%H%M%S");
  bool dst_flag_present = timestamp_str.size() > 14;
  if (dst_flag_present && timestamp_str[14] == 'S') {
    timestamp_tm.tm_isdst = 1;
  } else if (dst_flag_present && timestamp_str[14] == 'W') {
    timestamp_tm.tm_isdst = 0;
  } else {
    timestamp_tm.tm_isdst = -1;
  }
  std::time_t timestamp_unix = std::mktime(&timestamp_tm);
  std::cout << "Unix timestamp: " << timestamp_unix << std::endl;
  std::cout << "DST flag: " << timestamp_tm.tm_isdst << std::endl;
  return 0;
}