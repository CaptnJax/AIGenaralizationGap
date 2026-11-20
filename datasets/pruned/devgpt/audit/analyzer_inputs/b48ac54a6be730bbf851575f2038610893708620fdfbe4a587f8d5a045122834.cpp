void DescriptorPool::CopyDescriptors(VkDescriptorSet srcDescriptorSet, VkDescriptorSet dstDescriptorSet)
{
    VkCopyDescriptorSet copyDescriptorSet{};
    copyDescriptorSet.sType = VK_STRUCTURE_TYPE_COPY_DESCRIPTOR_SET;
    copyDescriptorSet.srcSet = srcDescriptorSet;
    copyDescriptorSet.dstSet = dstDescriptorSet;
    copyDescriptorSet.descriptorCount = 1;
    copyDescriptorSet.pNext = nullptr;
    vkUpdateDescriptorSets(m_pDevice->GetVkDevice(), 0, nullptr, 1, &copyDescriptorSet);
}