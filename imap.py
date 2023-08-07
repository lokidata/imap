import imaplib
import ssl
import email
import time
import schedule
import json
import logging
import os
import shutil
from logging.handlers import TimedRotatingFileHandler

level = {"debug":logging.DEBUG,"info":logging.INFO,'warning':logging.WARNING,'error':logging.ERROR}


def read_config(file):
    """
    Read a JSON configuration file.

    Args:
        file (str): the path of the file to read

    Returns:
        config (dict): a dictionary containing the configuration parameters
    """
    with open(file, encoding='utf-8') as c:
        config = json.load(c)
    return config

def copy_emails(account):
    """
    Copy unseen emails from the source account's inbox to the target account's inbox.

    Args:
        account (dict): A dictionary containing account information with keys:
            - "source_server", "source_port", "source_login", "source_password": Source email server details.
            - "target_server", "target_port", "target_login", "target_password": Target email server details.
            - "source_purge" (bool): Whether to purge source emails after copying.

    Returns:
        None
    """
    
    tls_context = ssl.create_default_context()
    
    for account_name, account_info in account.items():
        logger.info("polling account: " + account_name)
        
        logger.debug("connecting to the source server")
        try:
            source_mail = imaplib.IMAP4_SSL(host=account_info["source_server"],port=account_info["source_port"],ssl_context=tls_context) 
            source_mail.login(account_info["source_login"], account_info["source_password"])
            source_mail.select("inbox")
        except Exception as error:
            logger.error("Error while connecting to the source server: ", error)
            continue
        
        logger.debug("listing unseen email")
        _, email_ids = source_mail.search(None, "UNSEEN")
        email_ids = email_ids[0].split()
        
        logger.debug("connecting to the target server")
        try:
            target_mail = imaplib.IMAP4_SSL(host=account_info["target_server"],port=account_info["target_port"],ssl_context=tls_context) 
            target_mail.login(account_info["target_login"], account_info["target_password"])
            target_mail.select("inbox")
        except Exception as error:
            logger.error("Error while connecting to the target server: ", error)
            continue
        if email_ids:
            for email_id in email_ids:
                _, email_data = source_mail.fetch(email_id, "(RFC822)")
                msg = email.message_from_bytes(email_data[0][1])          
                target_mail.append("inbox", None, None, msg.as_bytes())
                logger.info("copyng email: " + msg['From'])
            
            if account_info["source_purge"]:
                logger.info("purge option selected, deleting seen email in source server")    
                source_mail.store(email_id, '+FLAGS', '\\Deleted') 
                source_mail.expunge()
        else:
            logger.info("No mail")
        source_mail.logout()
        target_mail.logout()
        
        
def first_run():
    
    if not os.path.exists("/config/config.json"):
        print("First run")
        shutil.copy("config.json", "/config/config.json")
        os.makedirs("/config/logs")
    else:
        print("config file already here")
        

def main():
    for account in accounts:
        copy_emails(account)

first_run()

param = read_config('/config/config.json')
logger = logging.getLogger()
logger.setLevel(level[param["loglevel"]])

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

sh = logging.StreamHandler()
sh.setLevel(level[param["loglevel"]])
sh.setFormatter(formatter)

handler = TimedRotatingFileHandler("/config/logs/imap.log", when='midnight', interval=1, backupCount=10)
handler.setLevel(level[param["loglevel"]])
handler.setFormatter(formatter)


logger.addHandler(handler)
logger.addHandler(sh)




accounts = param["accounts"]
logger.info("set schedule to: " + str(param["schedule_min"]) + " min")
schedule.every(param["schedule_min"]).minutes.do(main)

while True:
    schedule.run_pending()
    time.sleep(1)
