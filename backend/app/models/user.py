"""
User-related Pydantic models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .base import (
    BaseEntity,
    AuthProvider,
    SubscriptionTier,
    UserRole,
    Language,
)


class AccessibilitySettings(BaseModel):
    """User accessibility preferences."""
    
    enabled_features: List[str] = Field(
        default_factory=list,
        description="Enabled accessibility features"
    )
    font_size: str = Field(
        default="medium",
        description="Preferred font size"
    )
    contrast: str = Field(
        default="normal",
        description="Contrast preference"
    )
    color_scheme: str = Field(
        default="auto",
        description="Color scheme preference"
    )
    reduced_motion: bool = Field(
        default=False,
        description="Reduce motion animations"
    )
    screen_reader_optimized: bool = Field(
        default=False,
        description="Optimize for screen readers"
    )
    keyboard_navigation_only: bool = Field(
        default=False,
        description="Use keyboard navigation only"
    )
    
    @field_validator('font_size')
    @classmethod
    def validate_font_size(cls, v: str) -> str:
        """Validate font size option."""
        allowed_sizes = ['small', 'medium', 'large', 'extra-large']
        if v not in allowed_sizes:
            raise ValueError(f'Font size must be one of: {allowed_sizes}')
        return v
    
    @field_validator('contrast')
    @classmethod
    def validate_contrast(cls, v: str) -> str:
        """Validate contrast option."""
        allowed_contrasts = ['normal', 'high', 'extra-high']
        if v not in allowed_contrasts:
            raise ValueError(f'Contrast must be one of: {allowed_contrasts}')
        return v
    
    @field_validator('color_scheme')
    @classmethod
    def validate_color_scheme(cls, v: str) -> str:
        """Validate color scheme option."""
        allowed_schemes = ['light', 'dark', 'auto']
        if v not in allowed_schemes:
            raise ValueError(f'Color scheme must be one of: {allowed_schemes}')
        return v


class NotificationSettings(BaseModel):
    """User notification preferences."""
    
    email: bool = Field(default=True, description="Email notifications")
    push: bool = Field(default=True, description="Push notifications")
    sms: bool = Field(default=False, description="SMS notifications")
    job_completion: bool = Field(default=True, description="Job completion notifications")
    security_alerts: bool = Field(default=True, description="Security alert notifications")
    marketing_emails: bool = Field(default=False, description="Marketing email notifications")
    weekly_summary: bool = Field(default=True, description="Weekly summary emails")
    new_features: bool = Field(default=True, description="New feature announcements")


class PrivacySettings(BaseModel):
    """User privacy preferences."""
    
    allow_analytics: bool = Field(
        default=False,
        description="Allow usage analytics collection"
    )
    allow_model_training: bool = Field(
        default=False,
        description="Allow data use for model training"
    )
    share_usage_data: bool = Field(
        default=False,
        description="Share anonymized usage data"
    )
    data_retention_days: int = Field(
        default=30,
        ge=1, le=365,
        description="Data retention period in days"
    )
    export_data_on_deletion: bool = Field(
        default=True,
        description="Export data before account deletion"
    )


class UserPreferences(BaseModel):
    """User preferences and settings."""
    
    language: Language = Field(
        default=Language.ENGLISH,
        description="Preferred language"
    )
    jurisdiction: Optional[str] = Field(
        default=None,
        description="Default legal jurisdiction"
    )
    default_role: Optional[UserRole] = Field(
        default=None,
        description="Default user role for documents"
    )
    timezone: str = Field(
        default="UTC",
        description="User timezone"
    )
    date_format: str = Field(
        default="MM/DD/YYYY",
        description="Preferred date format"
    )
    time_format: str = Field(
        default="12h",
        description="Preferred time format"
    )
    currency: str = Field(
        default="USD",
        description="Preferred currency"
    )
    notifications: NotificationSettings = Field(
        default_factory=NotificationSettings,
        description="Notification preferences"
    )
    privacy: PrivacySettings = Field(
        default_factory=PrivacySettings,
        description="Privacy preferences"
    )
    accessibility: AccessibilitySettings = Field(
        default_factory=AccessibilitySettings,
        description="Accessibility preferences"
    )
    
    @field_validator('date_format')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format."""
        allowed_formats = ['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD']
        if v not in allowed_formats:
            raise ValueError(f'Date format must be one of: {allowed_formats}')
        return v
    
    @field_validator('time_format')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time format."""
        allowed_formats = ['12h', '24h']
        if v not in allowed_formats:
            raise ValueError(f'Time format must be one of: {allowed_formats}')
        return v


class UsageLimits(BaseModel):
    """Usage limits for a subscription tier."""
    
    documents: int = Field(gt=0, description="Monthly document limit")
    tokens: int = Field(gt=0, description="Monthly token limit")
    api_calls: int = Field(gt=0, description="Monthly API call limit")
    storage_bytes: int = Field(gt=0, description="Storage limit in bytes")
    export_downloads: int = Field(gt=0, description="Monthly export download limit")
    concurrent_jobs: int = Field(gt=0, description="Concurrent job limit")


class UserUsage(BaseModel):
    """User usage statistics and limits."""
    
    documents_processed: int = Field(
        default=0,
        ge=0,
        description="Documents processed this month"
    )
    total_tokens_used: int = Field(
        default=0,
        ge=0,
        description="Total tokens used this month"
    )
    api_calls_this_month: int = Field(
        default=0,
        ge=0,
        description="API calls made this month"
    )
    storage_used_bytes: int = Field(
        default=0,
        ge=0,
        description="Storage space used in bytes"
    )
    export_downloads_this_month: int = Field(
        default=0,
        ge=0,
        description="Export downloads this month"
    )
    last_active_at: Optional[datetime] = Field(
        default=None,
        description="Last activity timestamp"
    )
    monthly_limits: UsageLimits = Field(
        description="Current monthly limits"
    )
    usage_reset_date: datetime = Field(
        description="Date when usage counters reset"
    )
    
    @property
    def documents_remaining(self) -> int:
        """Calculate remaining document quota."""
        return max(0, self.monthly_limits.documents - self.documents_processed)
    
    @property
    def tokens_remaining(self) -> int:
        """Calculate remaining token quota."""
        return max(0, self.monthly_limits.tokens - self.total_tokens_used)
    
    @property
    def storage_remaining_bytes(self) -> int:
        """Calculate remaining storage quota."""
        return max(0, self.monthly_limits.storage_bytes - self.storage_used_bytes)


class UserSubscription(BaseModel):
    """User subscription information."""
    
    tier: SubscriptionTier = Field(
        default=SubscriptionTier.FREE,
        description="Subscription tier"
    )
    status: str = Field(
        default="active",
        description="Subscription status"
    )
    start_date: Optional[datetime] = Field(
        default=None,
        description="Subscription start date"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="Subscription end date"
    )
    auto_renew: bool = Field(
        default=False,
        description="Auto-renewal enabled"
    )
    payment_method: Optional[str] = Field(
        default=None,
        description="Payment method identifier"
    )
    billing_cycle: Optional[str] = Field(
        default=None,
        description="Billing cycle (monthly/yearly)"
    )
    next_billing_date: Optional[datetime] = Field(
        default=None,
        description="Next billing date"
    )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate subscription status."""
        allowed_statuses = ['active', 'inactive', 'cancelled', 'past_due', 'trialing']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v
    
    @field_validator('billing_cycle')
    @classmethod
    def validate_billing_cycle(cls, v: Optional[str]) -> Optional[str]:
        """Validate billing cycle."""
        if v is not None:
            allowed_cycles = ['monthly', 'yearly']
            if v not in allowed_cycles:
                raise ValueError(f'Billing cycle must be one of: {allowed_cycles}')
        return v
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return (
            self.status == 'active' and
            (self.end_date is None or self.end_date > datetime.utcnow())
        )


class User(BaseEntity):
    """User model."""
    
    uid: str = Field(description="Firebase user ID")
    email: Optional[str] = Field(default=None, description="User email")
    email_verified: bool = Field(default=False, description="Email verification status")
    display_name: Optional[str] = Field(default=None, description="Display name")
    photo_url: Optional[str] = Field(default=None, description="Profile photo URL")
    phone_number: Optional[str] = Field(default=None, description="Phone number")
    provider: AuthProvider = Field(description="Authentication provider")
    is_anonymous: bool = Field(default=False, description="Anonymous user flag")
    last_login_at: Optional[datetime] = Field(
        default=None,
        description="Last login timestamp"
    )
    preferences: UserPreferences = Field(
        default_factory=UserPreferences,
        description="User preferences"
    )
    usage: UserUsage = Field(description="Usage statistics and limits")
    subscription: UserSubscription = Field(
        default_factory=UserSubscription,
        description="Subscription information"
    )
    roles: List[str] = Field(
        default_factory=lambda: ['user'],
        description="User roles"
    )
    permissions: List[str] = Field(
        default_factory=list,
        description="User permissions"
    )
    is_active: bool = Field(default=True, description="Account active status")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional user metadata"
    )
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                raise ValueError('Invalid email format')
            return v.lower()
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is not None:
            import re
            # Basic international phone number validation
            cleaned = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not re.match(r'^\+?[1-9]\d{1,14}$', cleaned):
                raise ValueError('Invalid phone number format')
        return v
    
    @field_validator('photo_url')
    @classmethod
    def validate_photo_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate photo URL format."""
        if v is not None:
            import re
            if not re.match(r'^https?://.+', v):
                raise ValueError('Photo URL must be HTTP/HTTPS')
        return v
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions or 'admin' in self.roles
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles


class AuthState(BaseModel):
    """Authentication state."""
    
    is_authenticated: bool = Field(description="Authentication status")
    is_loading: bool = Field(default=False, description="Loading state")
    user: Optional[User] = Field(default=None, description="Authenticated user")
    token: Optional[str] = Field(default=None, description="Authentication token")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token")
    expires_at: Optional[datetime] = Field(default=None, description="Token expiration")
    error: Optional[str] = Field(default=None, description="Authentication error")


# Request/Response models
class LoginRequest(BaseModel):
    """Login request."""
    
    email: str = Field(description="User email")
    password: str = Field(min_length=8, description="User password")
    remember_me: bool = Field(default=False, description="Remember login")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()


class RegisterRequest(BaseModel):
    """Registration request."""
    
    email: str = Field(description="User email")
    password: str = Field(min_length=8, description="User password")
    display_name: str = Field(min_length=2, max_length=50, description="Display name")
    accept_terms: bool = Field(description="Terms acceptance")
    preferences: Optional[UserPreferences] = Field(
        default=None,
        description="Initial preferences"
    )
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        import re
        if not re.match(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
            v
        ):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one number, and one special character'
            )
        return v
    
    @field_validator('accept_terms')
    @classmethod
    def validate_terms_acceptance(cls, v: bool) -> bool:
        """Validate terms acceptance."""
        if not v:
            raise ValueError('Must accept terms and conditions')
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    
    email: str = Field(description="User email")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()


class UpdateProfileRequest(BaseModel):
    """Profile update request."""
    
    display_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="Display name"
    )
    photo_url: Optional[str] = Field(default=None, description="Profile photo URL")
    preferences: Optional[UserPreferences] = Field(
        default=None,
        description="Updated preferences"
    )
    
    @field_validator('photo_url')
    @classmethod
    def validate_photo_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate photo URL format."""
        if v is not None:
            import re
            if not re.match(r'^https?://.+', v):
                raise ValueError('Photo URL must be HTTP/HTTPS')
        return v


class UserStatsResponse(BaseModel):
    """User statistics response."""
    
    total_documents: int = Field(ge=0, description="Total documents processed")
    total_clauses: int = Field(ge=0, description="Total clauses analyzed")
    average_risk_score: float = Field(
        ge=0, le=1,
        description="Average risk score across documents"
    )
    most_common_role: Optional[UserRole] = Field(
        default=None,
        description="Most frequently used role"
    )
    favorite_jurisdiction: Optional[str] = Field(
        default=None,
        description="Most frequently used jurisdiction"
    )
    time_spent_minutes: int = Field(
        ge=0,
        description="Total time spent in application"
    )
    documents_by_risk: Dict[str, int] = Field(
        default_factory=dict,
        description="Document count by risk level"
    )
    monthly_activity: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Monthly activity data"
    )