void DescriptorPool::ExtendDescriptorPool()
{
    m_MaxDescriptorCount *= 2;
    VkDescriptorPool newDescriptorPool;
    CreateDescriptorPool(newDescriptorPool, m_MaxDescriptorCount);
    TransferDescriptors(newDescriptorPool);
    vkDestroyDescriptorPool(m_pDevice->GetVkDevice(), m_DescriptorPool, nullptr);
    m_DescriptorPool = newDescriptorPool;
}