int Stack::pop()
{
    if (top == nullptr)
    {
        cout << "Stack is empty" << endl;
        return -1;
    }
    int data = top->data;
    Node *temp = top;
    top = top->next;
    delete temp;
    return data;
}