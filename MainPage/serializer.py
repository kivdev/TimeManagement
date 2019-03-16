from rest_framework.serializers import ModelSerializer, SlugRelatedField

from MainPage.models import Affairs, Categories, Paterns, Icons
from Users.models import User


class CategoriesShortSerializer(ModelSerializer):
    class Meta:
        model = Categories
        fields = ("id", "name", "color")


class UserShortSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("email",)

class IconShortSerializer(ModelSerializer):

    class Meta:
        model = Icons
        fields = (
            "id",
            "path",
        )

class ItemSerializer(ModelSerializer):
    category = CategoriesShortSerializer()

    class Meta:
        model = Affairs
        fields = (
            'id',
            'start_date',
            'end_date',
            'start',
            'end',
            'category',
            'user',
            'complexity',
            'text',
            'importance',
            'status',
            'notifications',
            'notification_time',
            'period',
        )


class ItemAddSerializer(ModelSerializer):
    category = SlugRelatedField(many=False,
                                queryset=Categories.objects.all(),
                                slug_field='id')

    class Meta:
        model = Affairs
        fields = (
            'start_date',
            'end_date',
            'start',
            'end',
            'start_timestamp',
            'duration',
            'category',
            'user',
            'complexity',
            'text',
            'importance',
            'status',
            'notifications',
            'notification_time',
            'period',
        )


class ItemEditSerializer(ModelSerializer):
    category = SlugRelatedField(many=False,
                                queryset=Categories.objects.all(),
                                slug_field='id')

    class Meta:
        model = Affairs
        fields = (
            'start_date',
            'end_date',
            'start',
            'end',
            'start_timestamp',
            'duration',
            'category',
            'user',
            'complexity',
            'text',
            'importance',
            'status',
            'notifications',
            'notification_time',
            'period',
        )


class CategoriesSerializer(ModelSerializer):
    icon = IconShortSerializer()
    class Meta:
        model = Categories
        fields = (
            'id',
            'name',
            'icon',
            'categories',
            'color',
            'fast_access',
            'fast_access_index',
        )

class CategoriesAddSerializer(ModelSerializer):

    class Meta:
        model = Categories
        fields = (
            'name',
            'icon',
            'categories',
            'user',
            'color',
            'fast_access',
            'fast_access_index',
        )

class CategoriesEditSerializer(ModelSerializer):

    class Meta:
        model = Categories
        fields = (
            'name',
            'icon',
            'categories',
            'color',
            'fast_access',
            'fast_access_index',
        )


class PaternsSerializer(ModelSerializer):
    class Meta:
        model = Paterns
        fields = (
            'icon',
            'name',
            'affairs',
            'user',
        )


class PaternsAddSerializer(ModelSerializer):
    class Meta:
        model = Paterns
        fields = (
            'icon',
            'name',
            'affairs',
            'user',
        )
class PaternsEditSerializer(ModelSerializer):

    class Meta:
        model = Paterns
        fields = (
            'icon',
            'name',
            'affairs',
        )
