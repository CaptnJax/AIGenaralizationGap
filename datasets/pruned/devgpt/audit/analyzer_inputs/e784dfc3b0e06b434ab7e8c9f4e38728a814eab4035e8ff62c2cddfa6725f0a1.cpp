template <typename T>
Stack<T>::Stack(unsigned int stackSize)
{
    this->arr = new T[stackSize];
    this->cnt = 0;
    this->maxLen = stackSize;
}