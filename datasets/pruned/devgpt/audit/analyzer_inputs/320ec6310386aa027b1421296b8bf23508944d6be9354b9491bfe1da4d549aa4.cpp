std::string extract_cookie(const std::string& header) {
         size_t start_pos = header.find("Cookie: session_id=");
         if (start_pos == std::string::npos) return "";
         start_pos += 19;
         size_t end_pos = header.find(";", start_pos);
         if (end_pos == std::string::npos) end_pos = header.length();
         return header.substr(start_pos, end_pos - start_pos);
     }