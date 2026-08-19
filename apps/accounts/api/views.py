from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.api.serializers import (
    AvatarUploadSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

from apps.accounts.services.account_service import AccountService
from apps.accounts.services.auth_service import AuthService


class AuthViewSet(viewsets.ModelViewSet):

    queryset = User.objects.none()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):

        if self.action in ["register", "login"]:
            return [AllowAny()]

        return [IsAuthenticated()]

    def get_serializer_class(self):

        if self.action == "register":
            return RegisterSerializer

        if self.action == "login":
            return LoginSerializer

        if self.action == "avatar":
            return AvatarUploadSerializer

        if self.action == "change_password":
            return ChangePasswordSerializer

        return UserSerializer

    @action(
        detail=False,
        methods=["post"],
        authentication_classes=[],
        permission_classes=[AllowAny],
    )
    def register(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = AccountService.create_user(
            serializer.validated_data
        )

        data = AuthService.generate_tokens(user)

        return Response(
            {
                "message": "Registration successful",
                "access": data["access"],
                "refresh": data["refresh"],
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["post"],
        authentication_classes=[],
        permission_classes=[AllowAny],
    )
    def login(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = AuthService.login(
            serializer.validated_data["email"],
            serializer.validated_data["password"],
        )

        return Response(
            {
                "message": "Login successful",
                "access": data["access"],
                "refresh": data["refresh"],
                "user": UserSerializer(data["user"]).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["get", "patch"],
    )
    def me(self, request):

        if request.method == "GET":
            serializer = UserSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # PATCH — partial profile update. UserSerializer already marks
        # email/role/firebase_uid as read_only, so this can't be used
        # to self-elevate or hijack another account's email.
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
    )
    def avatar(self, request):

        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"url": request.user.photo.url if request.user.photo else None},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["post"],
    )
    def change_password(self, request):

        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Password updated."},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["post"],
    )
    def logout(self, request):

        refresh = request.data.get("refresh")

        AuthService.logout(refresh)

        return Response(
            {
                "message": "Logout successful",
            },
            status=status.HTTP_200_OK,
        )