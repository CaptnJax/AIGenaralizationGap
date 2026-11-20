static void dissect_ssh_decryptor(tvbuff_t *tvb, packet_info *pinfo, proto_tree *tree, void *data)
{
    col_set_str(pinfo->cinfo, COL_PROTOCOL, "SSHDECRYPTOR");
    col_clear(pinfo->cinfo,COL_INFO);
    proto_item *ti = proto_tree_add_item(tree, proto_ssh_decryptor, tvb, 0, -1, ENC_NA);
    proto_tree *ssh_decryptor_tree = proto_item_add_subtree(ti, ett_ssh_decryptor);
    guchar *decrypted_data;
    guint decrypted_data_len = 0;
    if (decrypt_ssh_payload(tvb_get_ptr(tvb, 0, -1), tvb_reported_length(tvb), &decrypted_data, &decrypted_data_len)) {
        proto_tree_add_bytes(ssh_decryptor_tree, hf_ssh_decrypted_payload, tvb, 0, decrypted_data_len, decrypted_data);
        col_add_fstr(pinfo->cinfo, COL_INFO, "SSH Decrypted Payload, Len: %u", decrypted_data_len);
    } else {
        col_add_fstr(pinfo->cinfo, COL_INFO, "SSH Decryption Failed");
    }
}