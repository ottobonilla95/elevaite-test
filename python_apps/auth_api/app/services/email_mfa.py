import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.models import User
from app.services.email_service import send_email


class EmailMFAService:
    def __init__(self):
        self.grace_period_days = settings.EMAIL_MFA_GRACE_PERIOD_DAYS
        self.auto_enable_method = settings.MFA_AUTO_ENABLE_METHOD
        self.primary_color = f"#{settings.MFA_EMAIL_PRIMARY_COLOR}"

    def _generate_mfa_code(self) -> str:
        """Generate a secure 6-digit MFA code."""
        return f"{secrets.randbelow(1000000):06d}"

    async def _store_mfa_code(
        self,
        user: "User",
        code: str,
        db: "AsyncSession",
        expires_in: int = 300,  # Change from 60 to 300 (5 minutes)
    ):
        """Store MFA code in database with expiration (5 minutes default)."""
        from sqlalchemy import update
        from datetime import datetime, timezone, timedelta

        expiry_time = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Update user with email MFA code and expiration
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(email_mfa_code=code, email_mfa_code_expires=expiry_time)
        )
        await db.execute(stmt)
        await db.commit()

    async def _get_mfa_code(self, user: "User") -> Optional[str]:
        """Retrieve MFA code from database and check expiration."""
        from datetime import datetime, timezone

        # Check if code exists and hasn't expired
        if not user.email_mfa_code or not user.email_mfa_code_expires:
            return None

        # Check if code has expired
        if datetime.now(timezone.utc) > user.email_mfa_code_expires:
            return None

        return user.email_mfa_code

    async def _delete_mfa_code(self, user: "User", db: "AsyncSession"):
        """Delete MFA code from database."""
        from sqlalchemy import update

        # Clear email MFA code and expiration
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(email_mfa_code=None, email_mfa_code_expires=None)
        )
        await db.execute(stmt)
        await db.commit()

    def _should_auto_enable_mfa(self, user: User) -> bool:
        """Check if MFA should be auto-enabled based on grace period."""
        if self.auto_enable_method == "none":
            return False

        # Check if user has "strong" MFA methods enabled
        has_strong_mfa = (
            user.email_mfa_enabled or user.sms_mfa_enabled or user.mfa_enabled  # TOTP
        )

        # Biometric alone is not considered sufficient for auto-enable bypass
        if has_strong_mfa:
            return False

        # If user only has biometric MFA, still auto-enable a stronger method
        # This ensures they have a backup method that works on all devices

        # Check grace period
        grace_period = timedelta(days=self.grace_period_days)
        now = datetime.now(timezone.utc)
        cutoff_date = now - grace_period

        user_created_at = user.created_at
        if user_created_at.tzinfo is None:
            user_created_at = user_created_at.replace(tzinfo=timezone.utc)

        return user_created_at < cutoff_date

    def get_grace_period_info(self, user: User) -> dict:
        """Get grace period information for a user."""
        try:
            # Validate grace period configuration
            if self.grace_period_days <= 0:
                logger.warning(f"Invalid grace period days: {self.grace_period_days}")
                return {
                    "in_grace_period": False,
                    "days_remaining": 0,
                    "grace_period_days": self.grace_period_days,
                    "expires_at": None,
                    "auto_enable_at": None,
                    "auto_enable_method": self.auto_enable_method,
                    "error": "Invalid grace period configuration",
                }

            # Check if the configured MFA method is already enabled
            mfa_already_enabled = False
            if self.auto_enable_method == "email" and user.email_mfa_enabled:
                mfa_already_enabled = True
            elif self.auto_enable_method == "sms" and user.sms_mfa_enabled:
                mfa_already_enabled = True
            elif self.auto_enable_method == "totp" and user.mfa_enabled:
                mfa_already_enabled = True
            elif self.auto_enable_method == "none":
                # If auto-enable is disabled, no grace period applies
                return {
                    "in_grace_period": False,
                    "days_remaining": 0,
                    "grace_period_days": self.grace_period_days,
                    "expires_at": None,
                    "auto_enable_at": None,
                    "auto_enable_method": self.auto_enable_method,
                }

            if mfa_already_enabled:
                return {
                    "in_grace_period": False,
                    "days_remaining": 0,
                    "grace_period_days": self.grace_period_days,
                    "expires_at": None,
                    "auto_enable_at": None,
                    "auto_enable_method": self.auto_enable_method,
                }

            # Validate user creation date
            if not user.created_at:
                logger.error(f"User {user.id} has no created_at timestamp")
                return {
                    "in_grace_period": False,
                    "days_remaining": 0,
                    "grace_period_days": self.grace_period_days,
                    "expires_at": None,
                    "auto_enable_at": None,
                    "auto_enable_method": self.auto_enable_method,
                    "error": "User creation date not available",
                }
        except Exception as e:
            logger.error(
                f"Error in grace period validation for user {user.id}: {str(e)}"
            )
            return {
                "in_grace_period": False,
                "days_remaining": 0,
                "grace_period_days": self.grace_period_days,
                "expires_at": None,
                "auto_enable_at": None,
                "auto_enable_method": self.auto_enable_method,
                "error": "Grace period calculation error",
            }

        try:
            # Calculate grace period expiration
            grace_period = timedelta(days=self.grace_period_days)

            # Use timezone-aware datetime for comparison
            now = datetime.now(timezone.utc)

            # Ensure user.created_at is timezone-aware for comparison
            user_created_at = user.created_at
            if user_created_at.tzinfo is None:
                # If user.created_at is naive, assume it's UTC
                user_created_at = user_created_at.replace(tzinfo=timezone.utc)

            grace_period_end = user_created_at + grace_period

            # Validate that grace period end is not in the past by more than reasonable amount
            # This handles edge cases where system clock might be off
            max_past_threshold = now - timedelta(days=365)  # 1 year ago
            if grace_period_end < max_past_threshold:
                logger.warning(
                    f"Grace period end date seems too far in the past for user {user.id}: {grace_period_end}"
                )

            # Check if still in grace period
            if now < grace_period_end:
                # Still in grace period
                time_remaining = grace_period_end - now
                days_remaining = max(0, time_remaining.days)

                # Handle edge case where time_remaining is very small
                if time_remaining.total_seconds() < 3600:  # Less than 1 hour
                    days_remaining = 0

                return {
                    "in_grace_period": True,
                    "days_remaining": days_remaining,
                    "grace_period_days": self.grace_period_days,
                    "expires_at": grace_period_end.isoformat(),
                    "auto_enable_at": grace_period_end.isoformat(),
                    "auto_enable_method": self.auto_enable_method,
                }
            else:
                # Grace period has expired
                return {
                    "in_grace_period": False,
                    "days_remaining": 0,
                    "grace_period_days": self.grace_period_days,
                    "expires_at": grace_period_end.isoformat(),
                    "auto_enable_at": grace_period_end.isoformat(),
                    "auto_enable_method": self.auto_enable_method,
                }
        except Exception as e:
            logger.error(f"Error calculating grace period for user {user.id}: {str(e)}")
            return {
                "in_grace_period": False,
                "days_remaining": 0,
                "grace_period_days": self.grace_period_days,
                "expires_at": None,
                "auto_enable_at": None,
                "auto_enable_method": self.auto_enable_method,
                "error": "Grace period calculation error",
            }

    async def _send_mfa_code_email(self, user: User, mfa_code: str) -> bool:
        """Send MFA code via email."""
        subject = "Your ElevAIte Login Code"

        text_body = f"""
        Hello {user.full_name or user.email},

        Your login verification code is: {mfa_code}

        This code will expire in 5 minutes. Please enter this code to complete your login.

        If you did not request this code, please ignore this email.

        Best regards,
        The {settings.BRANDING_ORG} Team
        """

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: {self.primary_color}; text-align: center;">ElevAIte Login Verification</h2>
                <p>Hello {user.full_name or user.email},</p>
                <p>Your login verification code is:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <div style="display: inline-block; background-color: #f8f9fa; border: 2px solid {self.primary_color}; border-radius: 10px; padding: 20px 40px;">
                        <span style="font-size: 36px; font-weight: bold; color: {self.primary_color}; letter-spacing: 8px;">{mfa_code}</span>
                    </div>
                </div>
                <p>This code will expire in 5 minutes. Please enter this code to complete your login.</p>
            </div>
        </body>
        </html>
        """
        user.email.lower().strip()
        return await send_email(user.email, subject, text_body, html_body)

    async def _send_auto_enabled_notification(self, user: User) -> bool:
        """Send notification that email MFA has been auto-enabled."""
        subject = "Email MFA Enabled for Your ElevAIte Account"

        text_body = f"""
        Hello {user.full_name or user.email},

        For enhanced security, email-based multi-factor authentication (MFA) has been automatically enabled for your ElevAIte account.

        From now on, when you log in, you'll receive a verification code via email that you'll need to enter to complete your login.

        This change was made because your account is older than {self.grace_period_days} days, and we're implementing additional security measures to protect your account.

        If you have any questions or concerns, please contact our support team.

        Best regards,
        The {settings.BRANDING_ORG} Team
        """

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: {self.primary_color}; text-align: center;">Email MFA Enabled</h2>
                <p>Hello {user.full_name or user.email},</p>
                <p>For enhanced security, email-based multi-factor authentication (MFA) has been automatically enabled for your ElevAIte account.</p>
                <div style="background-color: #f8f9fa; border-left: 4px solid {self.primary_color}; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>What this means:</strong></p>
                    <p style="margin: 5px 0 0 0;">When you log in, you'll receive a verification code via email that you'll need to enter to complete your login.</p>
                </div>
                <p>This change was made because your account is older than {self.grace_period_days} days, and we're implementing additional security measures to protect your account.</p>
                <p>If you have any questions or concerns, please contact our support team.</p>
                <p>Best regards,<br>The {settings.BRANDING_ORG} Team</p>
            </div>
        </body>
        </html>
        """

        return await send_email(user.email, subject, text_body, html_body)

    async def setup_email_mfa(self, user: User, db: AsyncSession) -> dict:
        """Set up email MFA for a user."""
        try:
            logger.info(f"Setting up email MFA for user {user.id}")

            # Generate and store MFA code
            mfa_code = self._generate_mfa_code()
            await self._store_mfa_code(user, mfa_code, db)

            # Send MFA code via email
            email_sent = await self._send_mfa_code_email(user, mfa_code)
            if not email_sent:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send verification email",
                )

            # Enable email MFA
            user.email_mfa_enabled = True
            await db.commit()
            await db.refresh(user)

            logger.info(f"Email MFA setup completed for user {user.id}")
            return {
                "message": "Email MFA enabled and verification code sent to your email",
                "email": user.email,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to setup email MFA for user {user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to setup email MFA",
            )

    async def send_mfa_code(self, user: User, db: "AsyncSession") -> dict:
        """Send MFA code to user's email."""
        if not user.email_mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email MFA is not enabled for this user",
            )

        try:
            logger.info(f"Sending email MFA code to user {user.id}")

            # Generate and store MFA code
            mfa_code = self._generate_mfa_code()
            await self._store_mfa_code(user, mfa_code, db)

            # Send MFA code via email
            email_sent = await self._send_mfa_code_email(user, mfa_code)
            if not email_sent:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send verification email",
                )

            logger.info(f"Email MFA code sent successfully to user {user.id}")
            return {
                "message": "MFA code sent successfully",
                "email": user.email,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to send email MFA code to user {user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send MFA code",
            )

    async def verify_mfa_code(
        self, user: User, provided_code: str, db: AsyncSession
    ) -> dict:
        """Verify MFA code provided by user."""
        if not user.email_mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email MFA is not enabled for this user",
            )

        try:
            logger.info(f"Verifying email MFA code for user {user.id}")

            stored_code = await self._get_mfa_code(user)
            if not stored_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No MFA code found or code has expired",
                )

            # Verify code
            if provided_code != stored_code:
                logger.warning(f"Invalid email MFA code provided for user {user.id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code"
                )

            # Delete used code
            await self._delete_mfa_code(user, db)

            logger.info(f"Email MFA verification successful for user {user.id}")
            return {"message": "Email MFA verification successful"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to verify email MFA for user {user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify MFA code",
            )

    async def disable_email_mfa(self, user: User, db: AsyncSession) -> dict:
        """Disable email MFA for a user."""
        user.email_mfa_enabled = False

        # Clean up any pending codes
        await self._delete_mfa_code(user, db)

        await db.commit()
        await db.refresh(user)

        logger.info(f"Email MFA disabled for user {user.id}")
        return {"message": "Email MFA disabled successfully"}

    async def check_and_auto_enable_mfa(self, user: User, db: AsyncSession) -> bool:
        """Check if MFA should be auto-enabled and enable it if needed."""
        if self._should_auto_enable_mfa(user):
            try:
                # Enable the configured MFA method
                if self.auto_enable_method == "email":
                    user.email_mfa_enabled = True
                    method_name = "Email MFA"
                elif self.auto_enable_method == "sms":
                    # Note: SMS MFA requires phone number setup, so this might not work
                    # without additional configuration
                    user.sms_mfa_enabled = True
                    method_name = "SMS MFA"
                elif self.auto_enable_method == "totp":
                    # Note: TOTP MFA requires secret setup, so this might not work
                    # without additional configuration
                    user.mfa_enabled = True
                    method_name = "TOTP MFA"
                else:
                    logger.warning(
                        f"Unknown auto-enable method: {self.auto_enable_method}"
                    )
                    return False

                await db.commit()
                await db.refresh(user)

                # Send notification email (only for email MFA for now)
                if self.auto_enable_method == "email":
                    await self._send_auto_enabled_notification(user)

                logger.info(
                    f"{method_name} auto-enabled for user {user.id} due to grace period expiry"
                )
                return True
            except Exception as e:
                logger.error(
                    f"Failed to auto-enable {self.auto_enable_method} MFA for user {user.id}: {str(e)}"
                )
                # Rollback the change if notification failed
                if self.auto_enable_method == "email":
                    user.email_mfa_enabled = False
                elif self.auto_enable_method == "sms":
                    user.sms_mfa_enabled = False
                elif self.auto_enable_method == "totp":
                    user.mfa_enabled = False
                await db.commit()
                return False

        return False


# Global service instance
email_mfa_service = EmailMFAService()
