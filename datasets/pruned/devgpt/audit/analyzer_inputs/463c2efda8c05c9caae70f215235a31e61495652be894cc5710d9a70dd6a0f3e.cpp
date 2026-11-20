template <typename T>
T Stack<T>::pop()
{
    if (this->cnt)
        return this->arr[--this->cnt];
    else
        return this->emptyValue;
}