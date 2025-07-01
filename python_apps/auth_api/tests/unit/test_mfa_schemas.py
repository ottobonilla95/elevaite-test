import pytest
from pydantic import ValidationError

from app.schemas.mfa import SMSMFASetupRequest, SMSMFAVerifyRequest, SMSMFAResponse


class TestSMSMFASetupRequest:
    def test_valid_setup_request(self):
        data = {"phone_number": "+1234567890"}
        request = SMSMFASetupRequest(**data)
        assert request.phone_number == "+1234567890"

    def test_phone_number_formatting(self):
        data = {"phone_number": "234-567-8901"}
        request = SMSMFASetupRequest(**data)
        assert request.phone_number == "+12345678901"

    def test_invalid_phone_number(self):
        data = {"phone_number": "123"}  # Too short
        with pytest.raises(ValidationError):
            SMSMFASetupRequest(**data)

    def test_missing_phone_number(self):
        with pytest.raises(ValidationError):
            SMSMFASetupRequest()


class TestSMSMFAVerifyRequest:
    def test_valid_verify_request(self):
        data = {"mfa_code": "123456"}
        request = SMSMFAVerifyRequest(**data)
        assert request.mfa_code == "123456"

    def test_invalid_mfa_code_length(self):
        data = {"mfa_code": "12345"}  # Too short
        with pytest.raises(ValidationError):
            SMSMFAVerifyRequest(**data)

    def test_invalid_mfa_code_format(self):
        data = {"mfa_code": "12345a"}  # Contains letter
        with pytest.raises(ValidationError):
            SMSMFAVerifyRequest(**data)

    def test_missing_mfa_code(self):
        with pytest.raises(ValidationError):
            SMSMFAVerifyRequest()


class TestSMSMFAResponse:
    def test_valid_response(self):
        data = {"message": "SMS MFA setup successful", "message_id": "msg_123456"}
        response = SMSMFAResponse(**data)
        assert response.message == "SMS MFA setup successful"
        assert response.message_id == "msg_123456"

    def test_minimal_response(self):
        data = {"message": "SMS MFA disabled"}
        response = SMSMFAResponse(**data)
        assert response.message == "SMS MFA disabled"
        assert response.message_id is None
