from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

class Hasher:
    @staticmethod
    def hash(password: str):
        return pwd_context.hash(password)

    @staticmethod
    def verify(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)