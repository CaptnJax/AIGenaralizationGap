void proto_register_ssh_decryptor(void)
{
    static hf_register_info hf[] = {
        { &hf_ssh_decrypted_payload,
          { "Decrypted Payload", "sshdecryptor.decrypted_payload",
            FT_BYTES, BASE_NONE, NULL, 0x0,
            NULL, HFILL }
        },
    };
    static gint *ett[] = {
        &ett_ssh_decryptor,
    };
    proto_ssh_decryptor = proto_register_protocol(
        SSH_DECRYPTOR_DESCRIPTION,
        "SSHDECRYPTOR",
        "sshdecryptor"
    );
    proto_register_field_array(proto_ssh_decryptor, hf, array_length(hf));
    proto_register_subtree_array(ett, array_length(ett));
}