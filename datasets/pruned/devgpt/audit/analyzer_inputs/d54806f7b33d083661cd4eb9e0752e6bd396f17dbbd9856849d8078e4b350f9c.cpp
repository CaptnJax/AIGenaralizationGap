void Scene::Update()
{
    std::set<std::pair<CollisionObject*, CollisionObject*>> previousCollisions;
    std::set<std::pair<CollisionObject*, CollisionObject*>> currentCollisions;
    for(auto& object : m_objects)
    {
        object->Update();
    }
    for (size_t i = 0; i < m_collisionObjects.size(); i++)
    {
        for (size_t j = i + 1; j < m_collisionObjects.size(); j++)
        {
            if (m_collisionObjects[i]->Intersects(m_collisionObjects[j]))
            {
                std::pair<CollisionObject*, CollisionObject*> collisionPair(m_collisionObjects[i], m_collisionObjects[j]);
                currentCollisions.insert(collisionPair);
                if (previousCollisions.find(collisionPair) == previousCollisions.end())
                {
                    m_collisionObjects[i]->GetOwner()->OnCollisionEnter(*m_collisionObjects[j]);
                    m_collisionObjects[j]->GetOwner()->OnCollisionEnter(*m_collisionObjects[i]);
                }
            }
            else
            {
                std::pair<CollisionObject*, CollisionObject*> collisionPair(m_collisionObjects[i], m_collisionObjects[j]);
                if (previousCollisions.find(collisionPair) != previousCollisions.end())
                {
                    m_collisionObjects[i]->GetOwner()->OnCollisionExit(*m_collisionObjects[j]);
                    m_collisionObjects[j]->GetOwner()->OnCollisionExit(*m_collisionObjects[i]);
                }
            }
        }
    }
    previousCollisions = currentCollisions;
}