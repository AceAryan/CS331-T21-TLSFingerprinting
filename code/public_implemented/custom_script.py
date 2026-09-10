import socket
import ssl

HOST = "www.google.com"
PORT = 443

# --------------------------------------------------
# 1. Create a TLS context
# --------------------------------------------------

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

# Certificate verification
context.verify_mode = ssl.CERT_REQUIRED
context.check_hostname = True
context.load_default_certs()

# --------------------------------------------------
# 2. Customize the TLS configuration
# --------------------------------------------------

# Force TLS 1.2
context.minimum_version = ssl.TLSVersion.TLSv1_2
context.maximum_version = ssl.TLSVersion.TLSv1_2

# Choose the cipher suites offered by our client
context.set_ciphers(
    "ECDHE-RSA-AES128-GCM-SHA256:"
    "ECDHE-RSA-AES256-GCM-SHA384"
)

# --------------------------------------------------
# 3. Create TCP connection
# --------------------------------------------------

print("[*] Connecting to", HOST)

sock = socket.create_connection((HOST, PORT))

print("[+] TCP connection established")

# --------------------------------------------------
# 4. Perform TLS handshake
# --------------------------------------------------

tls_sock = context.wrap_socket(
    sock,
    server_hostname=HOST
)

print("[+] TLS handshake completed")

# --------------------------------------------------
# 5. Display TLS information
# --------------------------------------------------

print()
print("TLS information")
print("----------------")
print("TLS version :", tls_sock.version())
print("Cipher      :", tls_sock.cipher())
print("Server name :", tls_sock.server_hostname)

# --------------------------------------------------
# 6. Send HTTP request over TLS
# --------------------------------------------------

request = (
    f"GET / HTTP/1.1\r\n"
    f"Host: {HOST}\r\n"
    f"Connection: close\r\n"
    f"\r\n"
)

tls_sock.sendall(request.encode())

print()
print("[+] HTTP request sent")

# --------------------------------------------------
# 7. Receive encrypted response
#    ssl module decrypts it for us
# --------------------------------------------------

print("[+] Receiving response...\n")

while True:
    data = tls_sock.recv(4096)

    if not data:
        break

    print(data.decode(errors="ignore"), end="")

# --------------------------------------------------
# 8. Close connection
# --------------------------------------------------

tls_sock.close()

print("\n\n[+] Connection closed")