from dataclasses import dataclass

@dataclass(frozen=True)
class RegisterRequest:
    email: str
    password: str

@dataclass(frozen=True)
class LoginRequest:
    email: str
    password: str
