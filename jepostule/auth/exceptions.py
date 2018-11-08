class AuthError(Exception):
    message = ''

class InvalidCredentials(AuthError):
    message = "Paramètres client ID/secret invalides"

class InvalidTimestamp(AuthError):
    message = "Paramètre 'timestamp' invalide"

class MissingParameter(AuthError):

    def __init__(self, name):
        super().__init__(name)
        self.message = "Paramètre manquant : '{}'".format(name)

class InvalidToken(AuthError):
    message = "Jeton d'authentification invalide"

class TokenExpiredError(AuthError):
    message = "Jeton d'authentification expiré"
