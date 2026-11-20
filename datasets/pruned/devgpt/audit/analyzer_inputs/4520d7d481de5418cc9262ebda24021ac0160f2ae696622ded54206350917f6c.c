int decrypt_ssh_payload(const guchar *encrypted_data, guint encrypted_data_len, guchar **decrypted_data, guint *decrypted_data_len) {
    if (encrypted_data == NULL || encrypted_data_len <= 0) {
        return 0;
    }
    const char *key = "your_key_here";
    const char *iv = "your_iv_here";
    size_t blklen = gcry_cipher_get_algo_blklen(GCRY_CIPHER_AES128);
    *decrypted_data_len = encrypted_data_len;
    *decrypted_data = (guchar *)malloc(*decrypted_data_len);
    if (*decrypted_data == NULL) {
        return 0;
    }
    gcry_cipher_hd_t hd;
    gcry_error_t err = gcry_cipher_open(&hd, GCRY_CIPHER_AES128, GCRY_CIPHER_MODE_CBC, 0);
    if (err) {
        free(*decrypted_data);
        return 0;
    }
    err = gcry_cipher_setkey(hd, key, blklen);
    if (err) {
        gcry_cipher_close(hd);
        free(*decrypted_data);
        return 0;
    }
    err = gcry_cipher_setiv(hd, iv, blklen);
    if (err) {
        gcry_cipher_close(hd);
        free(*decrypted_data);
        return 0;
    }
    err = gcry_cipher_decrypt(hd, *decrypted_data, *decrypted_data_len, encrypted_data, encrypted_data_len);
    gcry_cipher_close(hd);
    if (err) {
        free(*decrypted_data);
        return 0;
    }
    return 1;
}