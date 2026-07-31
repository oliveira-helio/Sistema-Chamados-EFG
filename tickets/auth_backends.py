from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from .models import normalize_matricula


User = get_user_model()


class EmailOrMatriculaBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or not password:
            return None

        try:
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(matricula__iexact=normalize_matricula(username))
            except User.DoesNotExist:
                for candidate in User.objects.all():
                    if normalize_matricula(candidate.matricula) == normalize_matricula(username):
                        user = candidate
                        break
                else:
                    return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
