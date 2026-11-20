void Stack::push(int data)
{
    Node *newNode = new Node;
    newNode->data = data;
    newNode->next = top;
    top = newNode;
}