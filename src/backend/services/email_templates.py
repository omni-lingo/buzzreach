"""Email templates for the onboarding module (ONBOARD-002).

Provides HTML and plain-text templates for verification, password reset,
and team invitation emails. Each function returns a (subject, html, text)
tuple ready for the SMTP sender.
"""


def verification_email(
    verify_url: str,
) -> tuple[str, str, str]:
    """Build a verification email.

    Args:
        verify_url: Full URL the user clicks to verify.

    Returns:
        Tuple of (subject, html_body, text_body).
    """
    subject = "Verify your BuzzReach email"
    html = _wrap_html(
        "Verify Your Email",
        (
            "<p>Welcome to BuzzReach! Please verify your email address "
            "by clicking the button below.</p>"
            f'{_button_html(verify_url, "Verify Email")}'
            "<p>This link expires in 6 hours.</p>"
            "<p>If you didn't create a BuzzReach account, "
            "you can safely ignore this email.</p>"
        ),
    )
    text = (
        "Welcome to BuzzReach!\n\n"
        "Please verify your email by visiting:\n"
        f"{verify_url}\n\n"
        "This link expires in 6 hours.\n\n"
        "If you didn't create a BuzzReach account, "
        "you can safely ignore this email."
    )
    return subject, html, text


def password_reset_email(
    reset_url: str,
) -> tuple[str, str, str]:
    """Build a password reset email.

    Args:
        reset_url: Full URL the user clicks to reset their password.

    Returns:
        Tuple of (subject, html_body, text_body).
    """
    subject = "Reset your BuzzReach password"
    html = _wrap_html(
        "Reset Your Password",
        (
            "<p>We received a request to reset your password. "
            "Click the button below to choose a new password.</p>"
            f'{_button_html(reset_url, "Reset Password")}'
            "<p>This link expires in 6 hours.</p>"
            "<p>If you didn't request a password reset, "
            "you can safely ignore this email.</p>"
        ),
    )
    text = (
        "Reset your BuzzReach password\n\n"
        "Visit this link to choose a new password:\n"
        f"{reset_url}\n\n"
        "This link expires in 6 hours.\n\n"
        "If you didn't request this, "
        "you can safely ignore this email."
    )
    return subject, html, text


def invitation_email(
    invite_url: str,
    team_name: str,
) -> tuple[str, str, str]:
    """Build a team invitation email.

    Args:
        invite_url: Full URL the invitee clicks to join.
        team_name: Display name of the team.

    Returns:
        Tuple of (subject, html_body, text_body).
    """
    subject = f"You're invited to join {team_name} on BuzzReach"
    html = _wrap_html(
        "Team Invitation",
        (
            f"<p>You've been invited to join <strong>{team_name}</strong> "
            "on BuzzReach.</p>"
            f'{_button_html(invite_url, "Accept Invitation")}'
            "<p>This invitation expires in 24 hours.</p>"
        ),
    )
    text = (
        f"You've been invited to join {team_name} on BuzzReach.\n\n"
        "Accept the invitation:\n"
        f"{invite_url}\n\n"
        "This invitation expires in 24 hours."
    )
    return subject, html, text


def _button_html(url: str, label: str) -> str:
    """Render a CTA button as inline-styled HTML."""
    return (
        '<table cellpadding="0" cellspacing="0" border="0" '
        'style="margin:24px 0"><tr><td>'
        f'<a href="{url}" style="'
        "background-color:#2563eb;color:#ffffff;"
        "padding:12px 32px;text-decoration:none;"
        "border-radius:6px;font-weight:600;"
        'display:inline-block">'
        f"{label}</a>"
        "</td></tr></table>"
    )


def _wrap_html(title: str, body_content: str) -> str:
    """Wrap body content in a minimal responsive HTML email layout."""
    return (
        "<!DOCTYPE html>"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width">'
        f"<title>{title}</title></head>"
        '<body style="margin:0;padding:0;font-family:'
        "Arial,Helvetica,sans-serif;background:#f4f4f5\">"
        '<table width="100%" cellpadding="0" cellspacing="0">'
        "<tr><td align=\"center\" style=\"padding:40px 16px\">"
        '<table width="100%" style="max-width:560px;'
        "background:#ffffff;border-radius:8px;"
        'padding:32px;border:1px solid #e4e4e7">'
        f"<tr><td><h1 style=\"margin:0 0 16px;font-size:22px\">"
        f"{title}</h1>{body_content}"
        "<p style=\"color:#71717a;font-size:13px;margin-top:32px\">"
        "&mdash; The BuzzReach Team</p>"
        "</td></tr></table></td></tr></table></body></html>"
    )
