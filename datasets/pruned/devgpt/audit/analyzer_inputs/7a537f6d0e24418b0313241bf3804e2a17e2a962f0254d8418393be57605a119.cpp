template <typename A, typename B, typename C>
PartialFunction<A, C> compose(PartialFunction<A, B> f, PartialFunction<B, C> g) {
    return [=](A a) -> std::optional<C> {
        std::optional<B> b = f(a);
        if(b.has_value())
            return g(b.value());
        else
            return std::nullopt;
    };
}