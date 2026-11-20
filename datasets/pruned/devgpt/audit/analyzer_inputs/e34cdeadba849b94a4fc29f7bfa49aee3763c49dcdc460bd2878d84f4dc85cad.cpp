int main()
{
    Stack<int> stack(5);
    try
    {
        stack.pop();
    }
    catch (const std::exception &ex)
    {
        std::cerr << "Exception: " << ex.what() << std::endl;
    }
    return 0;
}