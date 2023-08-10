import logging
import imaplib
import socket
import email
import time
import requests
from email.header import decode_header
import config as cfg
import json
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.message import MIMEMessage
import email
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)

def makeconnection(params):
        try:
            socket.setdefaulttimeout(5)
            if params['port']:
                imap_server = imaplib.IMAP4_SSL(
                    host=params['hostname'], port=params['port'])
            else:
                imap_server = imaplib.IMAP4_SSL(host=params['hostname'])
            login = imap_server.login(params['username'], params['password'])
            return login
        except socket.error as socketerror:
            logger.error(socketerror)
            return "Error: Provide valid inputs"
        except imaplib.IMAP4.error as e:
            logger.error(e)
            return "Error: Authentication Failed"
        except Exception as ge:
            logger.error(ge)
            return "Error: Provide valid inputs"

def readmessage(params):
    while(cfg.TIME_INTERVAL):
        logger.info("Checking any new emails...")    
        try:
            socket.setdefaulttimeout(5)
            if params['port']:
                imap_server = imaplib.IMAP4_SSL(
                    host=params['hostname'], port=params['port'])
            else:
                imap_server = imaplib.IMAP4_SSL(host=params['hostname'])
            imap_server.login(params['username'], params['password'])
            imap_server.select("INBOX")
            status, messages = imap_server.search(None, '(UNSEEN)')
            N = 1
            #for i in range(messages, messages-N, -1):
            for i in messages[0].split():
                # fetch the email message by ID
                res, msg = imap_server.fetch(i, "(RFC822)")
                for response in msg:
                    if isinstance(response, tuple):
                        # parse a bytes email into a message object
                        logger.info("New Email Received")
                        msg = email.message_from_bytes(response[1])                        
                        msg_id, encoding = decode_header(msg["Message-ID"])[0]
                        if isinstance(msg_id, bytes):
                            # if it's a bytes, decode to str
                            msg_id = msg_id.decode(encoding)
                            #logger.info(msg_id)
                        # decode the email subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            # if it's a bytes, decode to str
                            subject = subject.decode(encoding)
                            logger.info("Subject: %s", subject)
                        # decode email sender
                        From, encoding = decode_header(msg.get("From"))[0]
                        if isinstance(From, bytes):
                            From = From.decode(encoding)
                        #logger.info("From:", From)
                        # if the email message is multipart
                        if msg.is_multipart():
                            # iterate over email parts
                            for part in msg.walk():
                                # extract content type of email
                                content_type = part.get_content_type()
                                content_disposition = str(
                                    part.get("Content-Disposition"))
                                try:
                                    # get the email body
                                    #body = part.get_payload(
                                    #    decode=True).decode()
                                    body = part.get_payload(decode=False)
                                except:
                                    pass
                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    # print text/plain emails and skip attachments
                                    #logger.info(body)
                                    logger.info("Sent query to elevaite for processing")
                                    query_result = elevaitequery(str(body))
                                    logger.info("Query processed by elevaite")
                                    send_email(cfg.EMAIL_TO_LISTEN, From, subject, query_result, msg_id, msg)
                                    logger.info("Email response sent")
                                # elif "attachment" in content_disposition:
                                #     # download attachment
                                #     filename = part.get_filename()
                                #     if filename:
                                #         folder_name = clean(subject)
                                #         if not os.path.isdir(folder_name):
                                #             # make a folder for this email (named after the subject)
                                #             os.mkdir(folder_name)
                                #         filepath = os.path.join(
                                #             folder_name, filename)
                                #         # download attachment and save it
                                #         open(filepath, "wb").write(
                                #             part.get_payload(decode=True))
                        else:
                            # extract content type of email
                            content_type = msg.get_content_type()
                            # get the email body
                            body = msg.get_payload(decode=True).decode()
                            if content_type == "text/plain":
                                # print only text email parts
                                logger.info("Sent query to elevaite for processing")
                                query_result = elevaitequery(str(body))
                                logger.info("Query processed by elevaite")
                                send_email(cfg.EMAIL_TO_LISTEN, From, subject, query_result, msg_id, msg)
                                logger.info("Email response sent")
                        # if content_type == "text/html":
                        #     # if it's HTML, create a new HTML file and open it in browser
                        #     folder_name = clean(subject)
                        #     if not os.path.isdir(folder_name):
                        #         # make a folder for this email (named after the subject)
                        #         os.mkdir(folder_name)
                        #     filename = "index.html"
                        #     filepath = os.path.join(folder_name, filename)
                        #     # write the file
                        #     open(filepath, "w").write(body)
                        #     # open in the default browser
                        #     webbrowser.open(filepath)
                        print("="*100)
            # close the connection and logout                        
            imap_server.close()
            imap_server.logout()            
        except socket.error as socketerror:
            logger.error(socketerror)            
        except imaplib.IMAP4.error as e:
            logger.error(e)            
        except Exception as ge:
            logger.error(ge)            
        logger.info("Thread going to sleep for 60 seconds") 
        time.sleep(cfg.TIME_INTERVAL)

def elevaitequery(query1):
        print("Here is teh queryasldkfjaslkdfjlaskdjflksjd", query1)
        req_json = {'email_query':query1}
        headers = {'Content-Type' : 'application/json'}      
        data = requests.post(cfg.ELEVAITE_QUERY_API_URL, data = json.dumps(req_json), headers = headers)         
        resp = data.json()        
        jsonstring = json.dumps(resp)
        query_result = resp['text']     
        return query_result

def send_email(sender, recipient, subject, body, msgId, original_msg):
    message = MIMEMultipart("mixed")    
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = "Re: " + subject
    message['In-Reply-To'] = msgId
    message['References'] = msgId
    message.set_reply_to = sender
    
    actual_body = MIMEMultipart("alternative")
    actual_body.attach(MIMEText(body, "html"))
    message.attach(actual_body)
    #message.attach(MIMEText(body, 'html'))
    #message.attach(MIMEMessage(original_msg))
    message.attach(MIMEMessage(original_msg))
    #message.set_content(body)
    #message.add_alternative(body, subtype='html')
    # th_topic, encoding = decode_header(original_msg["Thread-Topic"])[0]
    # if isinstance(original_msg, bytes):
    #     # if it's a bytes, decode to str
    #     th_topic = original_msg.decode(encoding)
    # message['Thread-Topic'] = th_topic

    # th_index, encoding = decode_header(original_msg["Thread-Index"])[0]
    # if isinstance(original_msg, bytes):
    #     # if it's a bytes, decode to str
    #     th_index = original_msg.decode(encoding)
    # message['Thread-Index'] = th_index
    
    print("after attach")
    with smtplib.SMTP(cfg.SMTP_EMAIL_HOST, cfg.SMTP_EMAIL_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(cfg.EMAIL_TO_LISTEN, cfg.EMAIL_TOKEN)       
        #smtp.send_message(message)
        smtp.sendmail(sender, recipient, message.as_string())        
