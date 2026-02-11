from casnum import CasNum, one, two, viewer, enable_graphics
from Crypto.Util.number import bytes_to_long, long_to_bytes

def cn(n):
    return CasNum.get_n(n)

def generate_keys(e = CasNum.get_n(2**16+1), nbits=10):
    """Generate public and private keys."""
    a = cn(2**(nbits-1))
    b = cn(2**(nbits))
    p = CasNum.get_prime(a, b)
    q = CasNum.get_prime(a, b)
    n = p * q
    phi = (p - one) * (q - one)

    while CasNum.gcd(e, phi) != one:
        print(f"generated {p.__str__(), q.__str__()}")
        p = CasNum.get_prime(a, b)
        q = CasNum.get_prime(a, b)
        phi = (p - one) * (q - one)

    d = CasNum.inv_mod(e, phi)
    return (e, n), (d, n)

def rsa_encrypt(m, e, n):
    num_representation = cn(bytes_to_long(m.encode()))
    if num_representation >= n:
        raise ValueError("Cannot encrypt message. Use bigger keys")
    return CasNum.pow_mod(num_representation, e, n)

def rsa_decrypt(cipher, d, n):
    return CasNum.pow_mod(cipher, d, n)

if __name__ == "__main__":
    if enable_graphics:
        viewer.start()
    (e, n), (d, n) = generate_keys()
    plain = "hi"
    print(f"Encrypting: '{plain}'")
    cipher = rsa_encrypt(plain, e, n)
    print(f"This is the cipher:\t{cipher}")
    dec = rsa_decrypt(cipher, d, n)
    dec = long_to_bytes(int(dec))
    print(f"This is the decryption:\t{dec}")
    exit()
