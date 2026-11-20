template <typename T>
void Stack<T>::push(T val)
{
    if (this->cnt < this->maxLen)
        this->arr[this->cnt++] = val;
}