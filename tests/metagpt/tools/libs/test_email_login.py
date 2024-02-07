import os

import pytest

from metagpt.tools.libs.email_login import email_login_imap

# Configuration for the test IMAP servers
TEST_IMAP_SERVERS = {"outlook.com": "imap-mail.outlook.com"}

# Setup correct and incorrect email information
correct_email_address = "englishgpt@outlook.com"
correct_email_password = os.environ.get("outlook_email_password")
incorrect_email_address = "test@unknown.com"
incorrect_email_password = "incorrect_password"


@pytest.fixture
def imap_server_setup(mocker):
    # Use the mocker fixture to mock the MailBox class
    mock_mailbox = mocker.patch("metagpt.tools.libs.email_login.MailBox")
    mock_mail_instance = mocker.Mock()
    mock_mail_instance.login.return_value = mock_mail_instance
    mock_mailbox.return_value = mock_mail_instance
    return mock_mail_instance


def test_email_login_imap_success(imap_server_setup):
    # Mock successful login
    mailbox = email_login_imap(correct_email_address, correct_email_password)
    assert mailbox is not None
    # Correctly assert that the login method of the MailBox mock was called with the correct arguments
    imap_server_setup.login.assert_called_with(correct_email_address, correct_email_password)


def test_email_login_imap_failure_due_to_incorrect_server(imap_server_setup):
    # Attempt to login with an incorrect server
    mailbox = email_login_imap(incorrect_email_address, incorrect_email_password)
    assert mailbox is None


def test_email_login_imap_failure_due_to_wrong_credentials(imap_server_setup):
    # Configure mock to throw an exception to simulate login failure due to incorrect credentials
    imap_server_setup.login.side_effect = Exception("Login failed")
    # Attempt to login which should simulate a failure
    mailbox = email_login_imap(correct_email_address, incorrect_email_password)
    assert mailbox is None
    # Verify that the login method was called with the expected arguments
    imap_server_setup.login.assert_called_with(correct_email_address, incorrect_email_password)
