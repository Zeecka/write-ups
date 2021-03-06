import string
from wiener.RSAwienerHacker import hack_RSA
from Crypto.Cipher import AES,PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.number import inverse, isPrime
from fractions import gcd
from secretsharing import PlaintextToHexSecretSharer as SS
from secretsharing import *


# From given decrypt.py file
def decrypt(private_key, ciphertext):
    """Decrypt a message with a given private key.

    Takes in a private_key generated by Crypto.PublicKey.RSA, which must be of
    size exactly 4096

    If the ciphertext is invalid, return None
    """
    if len(ciphertext) < 512 + 16:
        return None
    msg_header = ciphertext[:512]
    msg_iv = ciphertext[512:512+16]
    msg_body = ciphertext[512+16:]
    try:
        symmetric_key = PKCS1_OAEP.new(private_key).decrypt(msg_header)
    except ValueError:
        return None
    if len(symmetric_key) != 32:
        return None
    return AES.new(symmetric_key, mode=AES.MODE_CFB, IV=msg_iv).decrypt(msg_body)


def create_private_key(p, q, public_key, d=None):
    if not d:
        assert(public_key.n % p == 0)
        assert(public_key.n % q == 0)
        print("[*] Valid p and q for given N. Calculating d.")
        d = inverse(public_key.e, (p-1)*(q-1))
    print("[*] Creating private key.")
    private_key = RSA.construct((public_key.n, public_key.e, d))
    return private_key


def get_message(private_key, encrypted_messages):
    for ciphertext in encrypted_messages:
        decrypted_text = decrypt(private_key, ciphertext)
        if decrypted_text:
            if all([x in string.printable for x in decrypted_text]):
                encrypted_messages.remove(ciphertext)
                print("[*] Found Plaintext, Messages remaining: " + str(len(encrypted_messages)))
                return decrypted_text


def isqrt(n):
    x = n
    y = (x + n // x) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def fermat(n, verbose=True):
    a = isqrt(n) # int(ceil(n**0.5))
    b2 = a*a - n
    b = isqrt(n) # int(b2**0.5)
    count = 0
    while b*b != b2:
        if verbose:
            print('Trying: a=%s b2=%s b=%s' % (a, b2, b))
        a += 1
        b2 = a*a - n
        b = isqrt(b2) # int(b2**0.5)
        count += 1
    print("[*] Found p, q with Fermet's")
    return a+b, a-b


def find_common_factor(public_keys):
    for key1 in public_keys:
        for key2 in public_keys:
            if key1.n != key2.n:
                g = gcd(key1.n, key2.n)
                if g != 1:
                    print "[*] Found common factor in modulus for two keys"
                    return g, key1, key2


def unsecret_num(num, secret_message):
        shares = []
        for i in range(len(secret_message)):
                sf = secret_message[i].split("\n") #each share is delineated by a newline character
                shares.append(sf[num]) #get share from file contents and add to share array
        return SS.recover_secret(shares).strip()

if __name__ == "__main__":
    public_keys = []
    for num in range(10):
        with open('RSABuffet/key-'+str(num)+ '.pem') as key_file:
            public_keys.append(RSA.importKey(key_file.read()))
    encrypted_messages = []
    for num in range(1, 6):
        ciphertextFile = 'RSABuffet/ciphertext-' + str(num) + ".bin"
        with open(ciphertextFile) as f:
            encrypted_messages.append(f.read())

    secret_messages = []
    print "===Breaking first key: Fermat's Attack (same size q and p) on key-1.pem==="
    p, q = fermat(public_keys[1].n, False)
    private_key = create_private_key(p, q, public_keys[1])
    secret_message = get_message(private_key, encrypted_messages).split('\n', 1)[1]
    secret_messages.append(secret_message)
    print('[*] Decrypted Message 1 "\n')

    print "===Breaking second key: Small p in key-2.pem ==="
    p = long(2758599203)
    q = public_keys[2].n / p
    private_key = create_private_key(p, q, public_keys[2])
    secret_message = get_message(private_key, encrypted_messages).split('\n', 1)[1]
    secret_messages.append(secret_message)
    print('[*] Decrypted Message 2 \n')

    print "===Breaking third key: Weiner's Attack on key-3.pem==="
    d = hack_RSA(public_keys[3].e, public_keys[3].n)
    private_key = create_private_key(None, None, public_keys[3], d)
    secret_message = get_message(private_key, encrypted_messages).split('\n', 1)[1]
    secret_messages.append(secret_message)
    print('[*] Decrypted Message 3 \n')

    print "===Breaking fourth key: Multi Key Attack on key-0 and key-6==="
    p, key1, key2 = find_common_factor(public_keys)
    private_key = create_private_key(p, key1.n / p, key1)
    secret_message = get_message(private_key, encrypted_messages).split('\n', 1)[1]
    secret_messages.append(secret_message)
    print('[*] Decrypted Message 4 \n')

    secret_messages = sorted(secret_messages)
    for num in range(len(secret_messages)):
        secret = unsecret_num(num, secret_messages)
        print("Message" + str(num+1) + ":\n" + secret + '\n')

