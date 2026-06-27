from dataclasses import dataclass
from html import escape

from navabe_api.domain.models import Admin, User

CANVAS_COLOR = "#eee9df"
PAPER_COLOR = "#f8f5ee"
INK_COLOR = "#20211e"
BRAND_COLOR = "#315b45"
LINE_COLOR = "#c8c0b2"
FOOTER_COLOR = "#2f2a24"
FOOTER_BORDER_COLOR = "#2a251f"
FOOTER_TEXT_COLOR = "#f8f5ee"
MUTED_TEXT_COLOR = "#686157"


@dataclass(frozen=True)
class EmailTemplate:
    subject: str
    text: str
    html: str


def customer_welcome_email(user: User) -> EmailTemplate:
    subject = "Welcome to Navabe Bookstore"
    text = (
        f"Hello {user.first_name},\n\n"
        "Welcome to Navabe Bookstore. Your customer account is ready.\n\n"
        f"Your Navabe Bookstore identifier is {user.identifier}.\n\n"
        "Keep this identifier for sign-ins and account recovery.\n\n"
        "The Navabe Bookstore team"
    )
    html = _layout(
        preheader=f"Your Navabe Bookstore identifier is {user.identifier}.",
        title="Welcome to Navabe Bookstore",
        greeting=f"Hello {user.first_name},",
        paragraphs=(
            "Your customer account is ready. You can now browse the catalog, "
            "place orders and manage your account with Navabe Bookstore.",
            "Keep this identifier somewhere safe. It is used for sign-ins and "
            "account recovery.",
        ),
        details=(("Customer identifier", user.identifier),),
        footer_note="This email confirms the creation of your Navabe Bookstore customer account.",
    )
    return EmailTemplate(subject, text, html)


def customer_password_changed_email(user: User) -> EmailTemplate:
    subject = "Navabe Bookstore password changed"
    text = (
        f"Hello {user.first_name},\n\n"
        "Your Navabe Bookstore password was changed.\n\n"
        "If you did not make this change, contact the Navabe Bookstore team immediately.\n\n"
        "The Navabe Bookstore team"
    )
    html = _layout(
        preheader="Your Navabe Bookstore password was changed.",
        title="Password changed",
        greeting=f"Hello {user.first_name},",
        paragraphs=(
            "Your Navabe Bookstore password was changed successfully.",
            "If you did not make this change, contact the Navabe Bookstore team immediately.",
        ),
        status="Security notice",
        footer_note="This security notification was sent to protect your account.",
    )
    return EmailTemplate(subject, text, html)


def customer_recovery_email(user: User, password: str) -> EmailTemplate:
    subject = "Navabe Bookstore account recovery"
    text = (
        f"Hello {user.first_name},\n\n"
        "A temporary password was generated for your Navabe Bookstore account.\n\n"
        f"Temporary password: {password}\n\n"
        "Use it to sign in, then change your password from your account settings.\n\n"
        "The Navabe Bookstore team"
    )
    html = _layout(
        preheader="A temporary password was generated for your Navabe Bookstore account.",
        title="Account recovery",
        greeting=f"Hello {user.first_name},",
        paragraphs=(
            "Use the temporary password below to sign in to your Navabe Bookstore account.",
            "For your security, change it from your account settings after signing in.",
        ),
        details=(("Temporary password", password),),
        sensitive_detail_labels=("Temporary password",),
        footer_note="You can ignore this email if you did not request account recovery.",
    )
    return EmailTemplate(subject, text, html)


def admin_welcome_email(admin: Admin, password: str) -> EmailTemplate:
    subject = "Welcome to the Navabe Bookstore Management Portal"
    text = (
        f"Hello {admin.first_name},\n\n"
        "Your Navabe Bookstore management account is ready.\n\n"
        f"Manager ID: {admin.identifier}\n"
        f"Temporary password: {password}\n\n"
        "Use these credentials to sign in, then replace the temporary password.\n\n"
        "The Navabe Bookstore team"
    )
    html = _layout(
        preheader=f"Your manager ID is {admin.identifier}.",
        title="Management account ready",
        greeting=f"Hello {admin.first_name},",
        paragraphs=(
            "Your Navabe Bookstore management account has been created.",
            "Use these credentials to sign in to the management portal, then replace "
            "the temporary password.",
        ),
        details=(("Manager ID", admin.identifier), ("Temporary password", password)),
        sensitive_detail_labels=("Temporary password",),
        status="Management access",
        footer_note="Keep these credentials private and do not forward this email.",
    )
    return EmailTemplate(subject, text, html)


def admin_recovery_email(admin: Admin, password: str) -> EmailTemplate:
    subject = "Navabe Bookstore management account recovery"
    text = (
        f"Hello {admin.first_name},\n\n"
        "A temporary password was generated for your Navabe Bookstore management account.\n\n"
        f"Temporary password: {password}\n\n"
        "Use it to sign in, then replace it from the management portal.\n\n"
        "The Navabe Bookstore team"
    )
    html = _layout(
        preheader="A temporary management password was generated.",
        title="Management recovery",
        greeting=f"Hello {admin.first_name},",
        paragraphs=(
            "Use the temporary password below to sign in to the Navabe Bookstore management portal.",
            "For your security, replace it as soon as you regain access.",
        ),
        details=(("Temporary password", password),),
        sensitive_detail_labels=("Temporary password",),
        status="Management access",
        footer_note="You can ignore this email if you did not request management recovery.",
    )
    return EmailTemplate(subject, text, html)


def admin_password_changed_email(admin: Admin) -> EmailTemplate:
    subject = "Navabe Bookstore management password changed"
    text = (
        f"Hello {admin.first_name},\n\n"
        "Your Navabe Bookstore management password was changed.\n\n"
        "If you did not make this change, contact the Navabe Bookstore team immediately.\n\n"
        "The Navabe Bookstore team"
    )
    html = _layout(
        preheader="Your Navabe Bookstore management password was changed.",
        title="Management password changed",
        greeting=f"Hello {admin.first_name},",
        paragraphs=(
            "Your Navabe Bookstore management password was changed successfully.",
            "If you did not make this change, contact the Navabe Bookstore team immediately.",
        ),
        status="Security notice",
        footer_note="This security notification was sent to protect your management account.",
    )
    return EmailTemplate(subject, text, html)


def _layout(
    *,
    preheader: str,
    title: str,
    greeting: str,
    paragraphs: tuple[str, ...],
    details: tuple[tuple[str, str], ...] = (),
    sensitive_detail_labels: tuple[str, ...] = (),
    status: str | None = None,
    footer_note: str,
) -> str:
    escaped_title = escape(title)
    paragraph_html = "".join(
        (
            f'<p style="margin:0 0 16px;color:{INK_COLOR};font-size:16px;'
            'line-height:1.55;">'
            f"{escape(paragraph)}</p>"
        )
        for paragraph in paragraphs
    )
    status_html = _status_badge(status) if status else ""
    details_html = _details_table(details, sensitive_detail_labels)

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="color-scheme" content="light">
    <meta name="supported-color-schemes" content="light">
    <title>{escaped_title}</title>
  </head>
  <body style="margin:0;padding:0;background:{CANVAS_COLOR};font-family:Georgia,'Times New Roman',serif;">
    <div style="display:none;max-height:0;overflow:hidden;color:{CANVAS_COLOR};opacity:0;">
      {escape(preheader)}
    </div>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CANVAS_COLOR};margin:0;padding:0;">
      <tr>
        <td align="center" style="padding:32px 16px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;background:{CANVAS_COLOR};border:1px solid {LINE_COLOR};overflow:hidden;">
            <tr>
              <td style="background:{PAPER_COLOR};border-bottom:1px solid {LINE_COLOR};padding:24px 28px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="vertical-align:middle;">
                      <span style="display:inline-block;width:40px;height:40px;background:{BRAND_COLOR};color:{PAPER_COLOR};font-size:22px;font-weight:700;line-height:40px;text-align:center;">N</span>
                      <span style="display:inline-block;margin-left:12px;color:{INK_COLOR};font-size:22px;font-weight:700;line-height:40px;vertical-align:top;">Navabe Bookstore</span>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:32px 28px 12px;">
                {status_html}
                <h1 style="margin:0 0 18px;color:{INK_COLOR};font-size:28px;line-height:1.25;font-weight:700;">{escaped_title}</h1>
                <p style="margin:0 0 16px;color:{INK_COLOR};font-size:16px;line-height:1.55;">{escape(greeting)}</p>
                {paragraph_html}
                {details_html}
              </td>
            </tr>
            <tr>
              <td style="padding:4px 28px 32px;">
                <p style="margin:0;color:{MUTED_TEXT_COLOR};font-size:14px;line-height:1.5;">{escape(footer_note)}</p>
              </td>
            </tr>
            <tr>
              <td style="background:{FOOTER_COLOR};border-top:1px solid {FOOTER_BORDER_COLOR};padding:18px 28px;text-align:right;">
                <p style="margin:0;color:{FOOTER_TEXT_COLOR};font-size:13px;line-height:1.5;">Navabe Bookstore<br>Catalog, customer accounts and management portal</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _status_badge(status: str) -> str:
    return (
        '<p style="display:inline-block;margin:0 0 14px;padding:6px 10px;'
        f"background:{BRAND_COLOR};color:{PAPER_COLOR};font-size:13px;"
        'font-weight:700;letter-spacing:0.04em;line-height:1.2;">'
        f"{escape(status)}</p>"
    )


def _details_table(
    details: tuple[tuple[str, str], ...],
    sensitive_detail_labels: tuple[str, ...],
) -> str:
    if not details:
        return ""

    rows = []
    sensitive_labels = set(sensitive_detail_labels)
    for label, value in details:
        value_style = (
            "font-family:'Courier New',Courier,monospace;font-size:18px;font-weight:700;"
            if label in sensitive_labels
            else "font-size:18px;font-weight:700;"
        )
        rows.append(
            "<tr>"
            f'<td style="padding:14px 16px;border-top:1px solid {LINE_COLOR};">'
            f'<p style="margin:0 0 4px;color:{MUTED_TEXT_COLOR};font-size:13px;line-height:1.35;">'
            f"{escape(label)}</p>"
            f'<p style="margin:0;color:{INK_COLOR};line-height:1.35;{value_style}">'
            f"{escape(value)}</p>"
            "</td>"
            "</tr>"
        )

    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="margin:22px 0 18px;background:{PAPER_COLOR};border:1px solid {LINE_COLOR};'
        'overflow:hidden;">'
        f"{''.join(rows)}"
        "</table>"
    )
