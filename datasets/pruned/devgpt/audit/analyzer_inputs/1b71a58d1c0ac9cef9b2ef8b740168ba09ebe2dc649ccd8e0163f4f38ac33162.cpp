vector<int> twoSum(vector<int>& nums, int target) {
    unordered_map<int, int> m;
    vector<int> result;
    for (int i = 0; i < nums.size(); i++) {
        int partner = target - nums[i];
        if (m.find(partner) != m.end()) {
            result.push_back(m[partner]);
            result.push_back(i);
            break;
        } else {
            m[nums[i]] = i;
        }
    }
    return result;
}