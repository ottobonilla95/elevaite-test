import logging
import config as cfg
import email_adapter as EmailConnection

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)


def read_email():
    params = getEmailConfig()
    EmailConnection.readmessage(params)
    return

def getEmailConfig():   
    email_params = {}
    email_params['hostname'] = cfg.IMAP_EMAIL_HOST
    email_params['username'] = cfg.EMAIL_TO_LISTEN
    email_params['password'] = cfg.EMAIL_TOKEN
    email_params['port'] = cfg.IMAP_EMAIL_PORT
    return email_params

if __name__ == "__main__":
    read_email()
