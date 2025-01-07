role_required_roles = {
    "read_all": ["PUBLIC"],
    "read_one": ["PUBLIC"],
    "create": ["PUBLIC"],
    "update": ["ADMIN"],
    "delete": ["ADMIN"]
}

user_required_roles = {
    "read_all": ["PUBLIC"],
    "read_one": ["PUBLIC"],
    "create": ["PUBLIC"],
    "update": ["ADMIN"],
    "delete": ["ADMIN"],
    "me": ["ADMIN"],
    "login": ["PUBLIC"],
    "register": ["ADMIN"],
    "verify": ["PUBLIC"],
    "logout": ["ADMIN"],
    "forgot-password": ["PUBLIC"],
    "reset-password": ["PUBLIC"],
    "change-password": ["ADMIN"]
}
