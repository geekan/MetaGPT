from metagpt.tools.libs.email_login import email_login_imap


def test_email_login(mocker):
    mock_mailbox = mocker.patch("metagpt.tools.libs.email_login.MailBox.login")
    mock_mailbox.login.return_value = mocker.Mock()
    email_login_imap("test@outlook.com", "test_password")
