from apps.accounts.models import User


class AccountService:

    @staticmethod
    def create_user(validated_data):
        """
        Create a user account.

        firebase_uid is handled separately because the current
        UserManager.create_user() does not accept it directly.
        """

        password = validated_data.pop("password", None)

        # Remove firebase_uid before passing data to UserManager
        firebase_uid = validated_data.pop("firebase_uid", None)

        # Create user using the existing UserManager
        user = User.objects.create_user(
            password=password,
            **validated_data,
        )

        # Set Firebase UID after user creation
        if firebase_uid:
            user.firebase_uid = firebase_uid
            user.save(update_fields=["firebase_uid"])

        return user

        AccountService._send_welcome_email(user)

        return user

    @staticmethod
    def _send_welcome_email(user):
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth.tokens import PasswordResetTokenGenerator
        from django.conf import settings
        import logging

        logger = logging.getLogger(__name__)

        try:
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            setup_link = f"{frontend_url}/setup-password?uid={uid}&token={token}"

            context = {
                "user": user,
                "setup_link": setup_link,
            }

            html_message = render_to_string("emails/welcome.html", context)
            
            send_mail(
                subject="Welcome to NeaPure - Account Created",
                message=f"Welcome {user.full_name}! Please set up your password at: {setup_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Welcome email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")

    @staticmethod
    def update_user(user, validated_data):

        for field, value in validated_data.items():
            setattr(user, field, value)

        user.save()

        return user

    @staticmethod
    def delete_user(user):
        user.delete()