from argon2 import PasswordHasher


password_hasher = PasswordHasher(
    time_cost=3,  # Number of iterations
    memory_cost=65536,  # 64MB memory usage
    parallelism=4,  # Number of parallel threads
    hash_len=32,  # Length of the hash in bytes
    salt_len=16,  # Length of the random salt in bytes
)

hashed_pass = "$argon2id$v=19$m=65536,t=3,p=4$uQSsEyyvJWzyjIKzm32u6Q$Ph2XgCtcatNLGxvmSzvw3nxWaf5GFAN+e+7Z3CUdzCQ"

current_pass = "Egk#eZ2!vb6d"

try:
    password_hasher.verify(hashed_pass, current_pass)
    print("Password matches")
except Exception as e:
    print("Password does not match")
