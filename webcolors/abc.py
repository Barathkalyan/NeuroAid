import bcrypt

password = "Test".encode("utf-8")
hashed = b"$2b$12$4xxIyp/nQlLBUN8uxoEq3ec.fxjkhVCEAT5v2REpRq2mnjjzez.ee"
print("Hello, NeuroAid!")


if bcrypt.checkpw(password, hashed):
    print(" Password matches")
else:
    print(" Password does not match")
