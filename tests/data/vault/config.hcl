storage "file" {
  path = "vault-data"
}

listener "tcp" {
  tls_disable = "true"
  # tls_cert_file = "yourdomain.crt"
  # tls_key_file  = "yourdomain.key"
}

ui = true