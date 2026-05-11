"""
Templates d'emails pour les campagnes de sensibilisation au phishing
"""

def build_tracking_link(base_url, campaign_id, user_id):
    """Construit le lien de tracking unique pour un utilisateur"""
    return f"{base_url}/track?cid={campaign_id}&uid={user_id}"


def build_email_content(user_email, tracking_link):
    """
    Template d'email basique (texte brut)
    
    Returns:
        tuple: (subject, body)
    """
    subject = "Important Security Update"

    body = f"""
Dear {user_email},

We detected unusual activity on your account.
Please verify your account immediately by clicking the link below:

{tracking_link}

IT Security Team
    """

    return subject, body


def build_html_email(user_email, tracking_link):
    """
    Template d'email HTML professionnel
    
    Returns:
        tuple: (subject, text_body, html_body)
    """
    subject = "🔒 Important: Security Alert on Your Account"
    
    # Version texte (fallback)
    text_body = f"""
SECURITY ALERT

Dear {user_email},

We have detected unusual activity on your account.

For your security, please verify your account by clicking the link below:
{tracking_link}

This is an urgent security measure to protect your account.

IT Security Team
Security Operations Center
    """
    
    # Version HTML
    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Alert</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px;">
        <tr>
            <td align="center">
                <!-- Main Container -->
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px;">
                                🔒 Security Alert
                            </h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 20px; color: #333; font-size: 16px;">
                                Dear <strong>{user_email}</strong>,
                            </p>
                            
                            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                <p style="margin: 0; color: #856404; font-size: 14px;">
                                    ⚠️ <strong>Unusual Activity Detected</strong><br>
                                    We have detected suspicious login attempts on your account.
                                </p>
                            </div>
                            
                            <p style="margin: 20px 0; color: #333; font-size: 16px;">
                                For your security, please verify your account immediately by clicking the button below:
                            </p>
                            
                            <!-- CTA Button -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{tracking_link}" 
                                           style="display: inline-block; padding: 15px 40px; background-color: #0078d4; color: #ffffff; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold;">
                                            Verify My Account Now
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 20px 0; color: #666; font-size: 14px;">
                                Or copy and paste this link into your browser:
                            </p>
                            
                            <p style="margin: 0; padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; word-break: break-all; font-size: 12px; color: #495057;">
                                {tracking_link}
                            </p>
                            
                            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                                <p style="margin: 0; color: #999; font-size: 12px;">
                                    <strong>Important:</strong> This is an urgent security measure. Failure to verify your account within 24 hours may result in temporary suspension.
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #dee2e6;">
                            <p style="margin: 0 0 10px; color: #666; font-size: 14px;">
                                <strong>IT Security Team</strong><br>
                                Security Operations Center
                            </p>
                            <p style="margin: 0; color: #999; font-size: 12px;">
                                © 2026 Security Operations. All rights reserved.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
    """
    
    return subject, text_body, html_body


# Templates alternatifs pour varier les campagnes
def build_password_reset_email(user_email, tracking_link):
    """Template : Réinitialisation de mot de passe"""
    subject = "Password Reset Request"
    
    text_body = f"""
Password Reset Request

Hello {user_email},

We received a request to reset your password.

Click here to reset your password:
{tracking_link}

If you didn't request this, please ignore this email.

Best regards,
Account Security Team
    """
    
    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2>Password Reset Request</h2>
    <p>Hello <strong>{user_email}</strong>,</p>
    <p>We received a request to reset your password.</p>
    <p>
        <a href="{tracking_link}" 
           style="display: inline-block; padding: 12px 30px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">
            Reset Password
        </a>
    </p>
    <p>If you didn't request this, please ignore this email.</p>
    <hr>
    <small>Account Security Team</small>
</body>
</html>
    """
    
    return subject, text_body, html_body


def build_payment_verification_email(user_email, tracking_link):
    """Template : Vérification de paiement"""
    subject = "⚠️ Payment Verification Required"
    
    text_body = f"""
Payment Verification Required

Dear {user_email},

We need to verify a recent payment on your account.

Please verify this transaction:
{tracking_link}

Thank you,
Billing Department
    """
    
    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f9f9f9;">
    <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px;">
        <h2 style="color: #dc3545;">⚠️ Payment Verification Required</h2>
        <p>Dear <strong>{user_email}</strong>,</p>
        <p>We need to verify a recent payment on your account to prevent fraud.</p>
        <p>
            <a href="{tracking_link}" 
               style="display: inline-block; padding: 12px 30px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px;">
                Verify Payment
            </a>
        </p>
        <p style="color: #666; font-size: 12px;">This verification must be completed within 24 hours.</p>
        <hr>
        <small>Billing Department</small>
    </div>
</body>
</html>
    """
    
    return subject, text_body, html_body
