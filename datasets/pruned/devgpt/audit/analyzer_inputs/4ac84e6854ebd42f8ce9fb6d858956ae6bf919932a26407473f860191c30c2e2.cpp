PYBIND11_MODULE(my_module, m) {
    py::class_<MyUnionWrapper>(m, "MyUnion")
        .def(py::init<>())
        .def("set_int", &MyUnionWrapper::set_int)
        .def("get_int", &MyUnionWrapper::get_int)
        .def("set_float", &MyUnionWrapper::set_float)
        .def("get_float", &MyUnionWrapper::get_float)
        .def("set_char", &MyUnionWrapper::set_char)
        .def("get_char", &MyUnionWrapper::get_char);
}