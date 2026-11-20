void DescriptorPool::AddEntity(Entity* entity)
{
    auto device = m_pDevice->GetVkDevice();
    if (m_CurrentDescriptorCount >= m_MaxDescriptorCount) {
        ExtendDescriptorPool();
    }
    VkDescriptorSetAllocateInfo allocInfo{};
    allocInfo.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    allocInfo.descriptorPool = m_DescriptorPool;
    allocInfo.descriptorSetCount = 1;
    allocInfo.pSetLayouts = &m_DescriptorSetLayout;
    if (vkAllocateDescriptorSets(device, &allocInfo, &entity->GetDescriptorSet()) != VK_SUCCESS) {
        throw std::runtime_error("failed to allocate descriptor sets!");
    }
    UpdateDescriptors(entity);
    m_CurrentDescriptorCount++;
}