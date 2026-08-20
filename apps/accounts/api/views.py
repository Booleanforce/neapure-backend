from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import (
    MultiPartParser,
    FormParser,
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response

from apps.accounts.models import User

from apps.accounts.api.serializers import (
    AvatarUploadSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
    PasswordSetupSerializer,
)

from apps.accounts.services.account_service import (
    AccountService,
)
from apps.accounts.services.auth_service import (
    AuthService,
)

from apps.accounts.permissions import (
    IsSuperAdmin,
)


class AuthViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    # ========================================================================
    # PERMISSIONS
    # ========================================================================

    def get_permissions(self):
        if self.action in [
            "register",
            "login",
            "setup_password",
        ]:
            return [
                AllowAny()
            ]

        if self.action in [
            "users",
            "retrieve",
            "destroy",
        ]:
            return [
                IsAuthenticated(),
                IsSuperAdmin(),
            ]

        return [
            IsAuthenticated()
        ]

    # ========================================================================
    # QUERYSET
    # ========================================================================

    def get_queryset(self):
        """
        Normal auth endpoints work with request.user.

        Super Admin user-management actions can access
        the complete User queryset.
        """

        if self.action in [
            "users",
            "retrieve",
            "destroy",
        ]:
            return (
                User.objects
                .all()
                .order_by("-created_at")
            )

        return User.objects.none()

    # ========================================================================
    # SERIALIZERS
    # ========================================================================

    def get_serializer_class(self):
        if self.action == "register":
            return RegisterSerializer

        if self.action == "login":
            return LoginSerializer

        if self.action == "setup_password":
            return PasswordSetupSerializer

        if self.action == "avatar":
            return AvatarUploadSerializer

        if self.action == "change_password":
            return ChangePasswordSerializer

        return UserSerializer

    # ========================================================================
    # REGISTER
    # ========================================================================

    @action(
        detail=False,
        methods=["post"],
        authentication_classes=[],
        permission_classes=[AllowAny],
    )
    def register(self, request):
        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = AccountService.create_user(
            serializer.validated_data
        )

        data = AuthService.generate_tokens(
            user
        )

        return Response(
            {
                "message": "Registration successful",
                "access": data["access"],
                "refresh": data["refresh"],
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

    # ========================================================================
    # LOGIN
    # ========================================================================

    @action(
        detail=False,
        methods=["post"],
        authentication_classes=[],
        permission_classes=[AllowAny],
    )
    def login(self, request):
        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = AuthService.login(
            serializer.validated_data["email"],
            serializer.validated_data["password"],
        )

        return Response(
            {
                "message": "Login successful",
                "access": data["access"],
                "refresh": data["refresh"],
                "user": UserSerializer(
                    data["user"]
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    # ========================================================================
    # CURRENT USER PROFILE
    # ========================================================================

    @action(
        detail=False,
        methods=["get", "patch"],
    )
    def me(self, request):
        if request.method == "GET":
            serializer = UserSerializer(
                request.user
            )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    # ========================================================================
    # SUPER ADMIN - ALL USERS
    # ========================================================================

    @action(
        detail=False,
        methods=["get"],
        url_path="users",
    )
    def users(self, request):
        """
        GET /api/auth/users/

        Returns all users for Super Admin.
        """

        queryset = self.get_queryset()

        serializer = UserSerializer(
            queryset,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    # ========================================================================
    # SUPER ADMIN - VIEW USER DETAILS
    # ========================================================================
    #
    # Uses standard DRF detail route:
    #
    # GET /api/auth/<id>/
    #
    # Since get_queryset() includes retrieve and permissions
    # require IsSuperAdmin, only Super Admin can access this.
    #
    # ========================================================================

    def retrieve(
        self,
        request,
        *args,
        **kwargs,
    ):
        user = self.get_object()

        serializer = self.get_serializer(
            user
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    # ========================================================================
    # SUPER ADMIN - PERMANENT DELETE
    # ========================================================================
    #
    # DELETE /api/auth/<id>/
    #
    # This permanently removes the User record.
    #
    # ========================================================================

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):
        user = self.get_object()

        deleted_id = str(user.id)
        deleted_email = user.email
        deleted_name = user.full_name

        # ---------------------------------------------------------------
        # Prevent accidental self deletion
        # ---------------------------------------------------------------

        if user.id == request.user.id:
            return Response(
                {
                    "success": False,
                    "message": (
                        "You cannot delete your own account."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------------
        # Delete related photo if present
        # ---------------------------------------------------------------

        if user.photo:
            try:
                user.photo.delete(
                    save=False
                )
            except Exception:
                pass

        # ---------------------------------------------------------------
        # Permanent deletion
        # ---------------------------------------------------------------

        user.delete()

        return Response(
            {
                "success": True,
                "message": (
                    "User deleted permanently."
                ),
                "deleted_id": deleted_id,
                "email": deleted_email,
                "name": deleted_name,
            },
            status=status.HTTP_200_OK,
        )

    # ========================================================================
    # AVATAR
    # ========================================================================

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[
            MultiPartParser,
            FormParser,
        ],
    )
    def avatar(self, request):
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.save()

        photo_url = None

        if user.photo:
            try:
                photo_url = user.photo.url
            except ValueError:
                photo_url = None

        return Response(
            {
                "url": photo_url,
            },
            status=status.HTTP_200_OK,
        )

    # ========================================================================
    # CHANGE PASSWORD
    # ========================================================================

    @action(
        detail=False,
        methods=["post"],
    )
    def change_password(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            {
                "message": "Password updated.",
            },
            status=status.HTTP_200_OK,
        )

    # ========================================================================
    # LOGOUT
    # ========================================================================

    @action(
        detail=False,
        methods=["post"],
    )
    def logout(self, request):
        refresh = request.data.get(
            "refresh"
        )

        AuthService.logout(
            refresh
        )

        return Response(
            {
                "message": "Logout successful",
            },
            status=status.HTTP_200_OK,
        )

    # ========================================================================
    # SETUP PASSWORD
    # ========================================================================

    @action(
        detail=False,
        methods=["post"],
        url_path="setup-password",
        authentication_classes=[],
        permission_classes=[AllowAny],
    )
    def setup_password(self, request):
        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.validated_data[
            "user"
        ]

        password = serializer.validated_data[
            "password"
        ]

        user.set_password(
            password
        )

        user.save(
            update_fields=[
                "password"
            ]
        )

        data = AuthService.generate_tokens(
            user
        )

        return Response(
            {
                "message": (
                    "Password setup successful"
                ),
                "access": data["access"],
                "refresh": data["refresh"],
                "user": UserSerializer(
                    user
                ).data,
            },
            status=status.HTTP_200_OK,
        )