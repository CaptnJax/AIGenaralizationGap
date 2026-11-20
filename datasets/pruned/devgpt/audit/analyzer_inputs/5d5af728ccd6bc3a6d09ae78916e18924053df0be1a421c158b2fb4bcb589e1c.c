void proto_reg_handoff_ssh_decryptor(void)
{
    static dissector_handle_t ssh_decryptor_handle;
    ssh_decryptor_handle = create_dissector_handle(dissect_ssh_decryptor, proto_ssh_decryptor);
    dissector_add_uint("ssh.port", 22, ssh_decryptor_handle);
}