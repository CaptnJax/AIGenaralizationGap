int main()
{
    Stack s;
    s.push(5);
    s.push(7);
    s.push(-3);
    cout << s.pop() << endl;
    s.push(9);
    while(s.top != nullptr)
        cout << s.pop() << endl;
    return 0;
}