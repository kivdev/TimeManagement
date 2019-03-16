from rest_framework.serializers import ModelSerializer

from .models import User, Tokenaizer

class UserShortSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ("email",)

class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ("email","password","is_admin","is_staff")

class TokenaizerSerializer(ModelSerializer):

    class Meta:
        model = Tokenaizer
        fields = ("user", "token")