template <typename T>
void Stack<T>::push(const T &val)
{
    if (this->cnt < this->maxLen)
        this->arr[this->cnt++] = val;
}