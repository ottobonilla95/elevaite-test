"""Biometric MFA router."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tenant_db import get_tenant_session
from app.schemas.user import (
    BiometricDeviceResponse,
    BiometricRegisterRequest,
)
from app.core.security import oauth2_scheme, verify_token
from app.db.models import User, BiometricDevice
from sqlalchemy.future import select
from app.core.mfa_validator import ensure_at_least_one_mfa

router = APIRouter(prefix="/biometric", tags=["biometric"])


@router.get("/devices", response_model=List[BiometricDeviceResponse])
async def get_biometric_devices(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Get all biometric devices for the current user."""
    # Verify token and get user_id
    payload = verify_token(token, "access")
    user_id = int(payload["sub"])
    
    # Get all active devices for this user
    result = await session.execute(
        select(BiometricDevice)
        .where(BiometricDevice.user_id == user_id)
        .where(BiometricDevice.is_active)
        .order_by(BiometricDevice.created_at.desc())
    )
    devices = result.scalars().all()
    
    return devices


@router.post("/register", response_model=BiometricDeviceResponse)
async def register_biometric_device(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Register a new biometric device for the current user."""
    # Verify token and get user_id
    payload = verify_token(token, "access")
    user_id = int(payload["sub"])
    
    # Parse request body manually
    body = await request.json()
    
    # Validate using Pydantic
    try:
        device_data = BiometricRegisterRequest(**body)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request data: {str(e)}"
        )
    
    # Check if device already exists
    result = await session.execute(
        select(BiometricDevice).where(
            BiometricDevice.device_fingerprint == device_data.device_fingerprint
        )
    )
    existing_device = result.scalars().first()
    
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device already registered"
        )
    
    # Create new device
    new_device = BiometricDevice(
        user_id=user_id,
        device_fingerprint=device_data.device_fingerprint,
        device_name=device_data.device_name,
        device_model=device_data.device_model,
        public_key=device_data.public_key,
        is_active=True,
        ip_address_at_registration=request.client.host if request.client else None,
        user_agent_at_registration=request.headers.get("user-agent"),
    )
    
    session.add(new_device)
    
    # Enable biometric MFA for user if not already enabled
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if user and not user.biometric_mfa_enabled:
        user.biometric_mfa_enabled = True
    
    await session.commit()
    await session.refresh(new_device)
    
    return new_device


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_biometric_device(
    device_id: int,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Remove a biometric device."""
    # Verify token and get user_id
    payload = verify_token(token, "access")
    user_id = int(payload["sub"])
    
    # Get the device
    result = await session.execute(
        select(BiometricDevice).where(
            BiometricDevice.id == device_id,
            BiometricDevice.user_id == user_id
        )
    )
    device = result.scalars().first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Delete the device
    await session.delete(device)
    
    # Check if user has any other biometric devices
    result = await session.execute(
        select(BiometricDevice).where(
            BiometricDevice.user_id == user_id,
            BiometricDevice.is_active
        )
    )
    remaining_devices = result.scalars().all()
    
    # If no devices left, disable biometric MFA
    if not remaining_devices:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.biometric_mfa_enabled = False
    
    await session.commit()
    
    return None

@router.post("/toggle-setting")
async def toggle_biometric_setting(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Toggle biometric MFA setting (for web app)."""
    # Parse the request body manually
    body = await request.json()
    enabled = body.get("enabled")
    
    if enabled is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="enabled field is required"
        )
    
    payload = verify_token(token, "access")
    user_id = int(payload["sub"])
    
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate BEFORE making changes
    if not enabled:
        print("🔍 User MFA status before disable:")
        print(f"  - Email MFA: {user.email_mfa_enabled}")
        print(f"  - SMS MFA: {user.sms_mfa_enabled}")
        print(f"  - TOTP MFA: {user.mfa_enabled}")
        print(f"  - Biometric MFA: {user.biometric_mfa_enabled}")
        ensure_at_least_one_mfa(user, 'biometric')
    
    # Update flag
    user.biometric_mfa_enabled = enabled
    
    # Delete devices if disabling
    if not enabled:
        devices_result = await session.execute(
            select(BiometricDevice).where(BiometricDevice.user_id == user_id)
        )
        devices = devices_result.scalars().all()
        
        for device in devices:
            await session.delete(device)
    
    await session.commit()
    
    return {
        "message": f"Biometric MFA {'enabled' if enabled else 'disabled'}",
        "biometric_mfa_enabled": enabled
    }

@router.post("/enable")
async def enable_biometric_mfa(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Enable biometric MFA flag (used by mobile app before device registration)."""
    payload = verify_token(token, "access")
    user_id = int(payload["sub"])
    
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.biometric_mfa_enabled = True
    await session.commit()
    
    return {
        "success": True,
        "message": "Biometric MFA enabled",
        "biometric_mfa_enabled": True
    }


@router.post("/disable")
async def disable_biometric_mfa(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_tenant_session),
):
    """Disable biometric MFA flag (used by mobile app)."""
    payload = verify_token(token, "access")
    user_id = int(payload["sub"])
    
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate at least one MFA remains
    print("🔍 User MFA status before disable:")
    print(f"  - Email MFA: {user.email_mfa_enabled}")
    print(f"  - SMS MFA: {user.sms_mfa_enabled}")
    print(f"  - TOTP MFA: {user.mfa_enabled}")
    print(f"  - Biometric MFA: {user.biometric_mfa_enabled}")
    ensure_at_least_one_mfa(user, 'biometric')
    
    user.biometric_mfa_enabled = False
    
    # Also delete all devices
    devices_result = await session.execute(
        select(BiometricDevice).where(BiometricDevice.user_id == user_id)
    )
    devices = devices_result.scalars().all()
    
    for device in devices:
        await session.delete(device)
    
    await session.commit()
    
    return {
        "success": True,
        "message": "Biometric MFA disabled",
        "biometric_mfa_enabled": False
    }