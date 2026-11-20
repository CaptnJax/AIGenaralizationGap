void DescriptorPool::TransferDescriptors(VkDescriptorPool& newDescriptorPool)
{
    for (u32 i = 0; i < MAX_FRAMES_IN_FLIGHT; ++i) {
        for (u32 j = 0; j < m_Entities.size(); ++j) {
            VkDescriptorSet oldDescriptorSet = m_Entities[j]->GetDescriptorSets()[i];
            VkDescriptorSetAllocateInfo allocInfo{};
            allocInfo.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
            allocInfo.descriptorPool = newDescriptorPool;
            allocInfo.descriptorSetCount = 1;
            allocInfo.pSetLayouts = &m_DescriptorSetLayout;
            if (vkAllocateDescriptorSets(m_pDevice->GetVkDevice(), &allocInfo, &(m_Entities[j]->GetDescriptorSets()[i])) != VK_SUCCESS) {
                throw std::runtime_error("failed to allocate descriptor sets!");
            }
            CopyDescriptors(oldDescriptorSet, m_Entities[j]->GetDescriptorSets()[i]);
            vkFreeDescriptorSets(m_pDevice->GetVkDevice(), m_DescriptorPool, 1, &oldDescriptorSet);
        }
    }
}