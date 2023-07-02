# django_project/users/tokens.py
# For generating token for verification
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six  # To ensure compatibility between Python versions

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp)  + six.text_type(user.is_active)
        )

account_activation_token = AccountActivationTokenGenerator()