template <typename T>
Stack<T>::~Stack()
{
    delete[] this->arr;
}