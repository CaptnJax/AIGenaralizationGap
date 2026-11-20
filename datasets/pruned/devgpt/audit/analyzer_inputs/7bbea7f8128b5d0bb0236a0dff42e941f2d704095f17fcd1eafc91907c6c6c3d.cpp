int Queue::dequeue() {
    if (front == nullptr) {
        cout << "The Queue is empty" << endl;
        return -1;
    } else {
        Node *temp = front;
        int data = temp->data;
        front = front->next;
        delete temp;
        return data;
    }
}