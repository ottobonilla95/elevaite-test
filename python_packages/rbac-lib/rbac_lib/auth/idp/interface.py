from abc import ABC, abstractmethod


class IDPInterface(ABC):
    @abstractmethod
    def get_user_email(self, access_token: str) -> str:
        """
        Retrieve user email from decoded access token response.

        Args:
        access_token (str): The access token for the IDP

        Returns:
        user corresponding to decoded access token

        Raises:
        NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError(
            "iDP Subclasses must implement this method to decode access token"
        )
