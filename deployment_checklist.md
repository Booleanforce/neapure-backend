# 🚀 Deployment Checklist & Feature Documentation

This document serves as a reference for the **User Credential Email** and **Self Profile Management** features to ensure smooth deployments and prevent future issues.

## 1. Environment Configurations (Action Required Before Production)

Before deploying this code to a live server, ensure these settings are updated in your environment:

### `EMAIL_BACKEND`
*   **Current State (Development):** Set to `django.core.mail.backends.console.EmailBackend` in `config/settings.py`. This is why emails are currently printing in your terminal instead of actually being sent.
*   **Production Requirement:** Revert this to use your actual SMTP provider (e.g., SendGrid, AWS SES) so real users receive their setup emails.
    ```python
    # Example Production Setting
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    ```

### `FRONTEND_URL`
*   **Current State (Development):** The backend relies on the `FRONTEND_URL` setting (defaulting to `http://localhost:3000`) to construct the password setup links in the welcome email.
*   **Production Requirement:** Ensure your production `.env` file explicitly defines the live frontend URL so the links route to the actual website.
    ```env
    FRONTEND_URL=https://www.neapure.com
    ```

---

## 2. Security Behaviors & Expected Outcomes

### One-Time Magic Links
*   The password setup link uses Django's `PasswordResetTokenGenerator`. 
*   **Behavior:** The token is cryptographically tied to the user's *current* password hash. 
*   **What this means:** As soon as the user successfully sets their password, the token is instantly invalidated. If they (or someone else) click the original email link again, the frontend will correctly display an error ("Link Expired / Invalid"). This is intended behavior and ensures maximum security.

### Profile Updates (`PATCH /api/users/profile/`)
*   **Behavior:** The `UserProfileUpdateSerializer` intentionally ignores sensitive fields.
*   **What this means:** If a frontend developer accidentally (or a malicious user intentionally) submits fields like `"role": "ADMIN"`, `"email": "hacker@neapure.com"`, or `"is_staff": true` in the JSON payload, the backend will completely ignore them.
*   **Allowed Fields:** Only `full_name`, `phone`, and `photo` will be saved to the database through this endpoint.

---

## 3. Creating Users

### The `AccountService` Standard
*   All programmatic user creation should continue to be routed through `AccountService.create_user(validated_data)`.
*   This service acts as the central hub for user creation, guaranteeing that passwords are set correctly, roles are validated, and the welcome email is triggered appropriately.

### Django Admin Panel Override
*   If your staff manually creates a user directly from the raw Django Admin Panel (`http://localhost:8000/admin/`), the welcome email **will** still be sent! 
*   I have overridden the `save_model` method in `apps/accounts/admin.py` to ensure this happens automatically without any extra steps.
