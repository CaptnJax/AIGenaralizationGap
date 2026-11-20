template <typename T>
Stack<T>::Stack(unsigned int stackSize, const T &emptyVal)
{
    this->arr = new T[stackSize];
    this->cnt = 0;
    this->maxLen = stackSize;
    this->emptyValue = emptyVal;
}