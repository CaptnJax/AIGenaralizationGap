void square(long& a, long& b, long& c, long& d){
    int a_tmp, b_tmp, c_tmp, d_tmp;
    a_tmp = a*a + b*b;
    b_tmp = a*c + b*d;
    c_tmp = c*a + d*b;
    d_tmp = c*c + d*d;
    a = a_tmp;
    b = b_tmp;
    c = c_tmp;
    d = d_tmp;
    return;
}