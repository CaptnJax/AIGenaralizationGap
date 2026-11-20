int main() {
    Queue q;
    q.enqueue(5);
    q.enqueue(7);
    q.enqueue(-3);
    cout << q.dequeue() << endl;
    q.enqueue(9);
    while (q.front != nullptr)
        cout << q.dequeue() << endl;
    return 0;
}