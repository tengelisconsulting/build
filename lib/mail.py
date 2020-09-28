import base64
from email.mime.text import MIMEText
import logging
from queue import Queue
from typing import Dict
from typing import List

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource

from .apptypes import BuildConf
from .env import ENV


MAGIC_GMAIL_USER_ID = "me"

MAIL_SERVICE: Resource
SUBS: List[str] = []


def init_mail(failure_q: Queue) -> None:
    logging.info("initing mail with creds %s", ENV.GMAIL_CREDS_F)
    creds = service_account.Credentials.from_service_account_file(
        ENV.GMAIL_CREDS_F,
        scopes=["https://mail.google.com/"]
    )
    creds = creds.with_subject(ENV.GMAIL_SEND_ADDR)
    service = build("gmail", "v1", credentials=creds)
    global MAIL_SERVICE
    MAIL_SERVICE = service
    global SUBS
    SUBS = [sub for sub in ENV.BUILD_FAILURE_SUBSCRIBERS.split(",") if sub]
    logging.info("mail service loaded, subscribers: %s", SUBS)
    while True:
        try:
            failure = failure_q.get()
            _on_failure(failure)
        except Exception as e:
            logging.exception("failed sending build failure notif: {}"
                              .format(e))
    return


# private
def _on_failure(
        build: BuildConf
) -> None:
    subject = f"Build failure {build.proj_name}"
    build_log = ""
    try:
        with open(build.log_file, "r") as f:
            build_log = f.read()
    except Exception as e:
        logging.exception("failed to read build log: {}".format(e))
        build_log = "couldn't read build log"
    msgs = [_create_message(
        to_email=addr,
        msg_subject=subject,
        msg_text=build_log
    ) for addr in SUBS]
    ress = [_send_msg(msg) for msg in msgs]
    logging.info("sent build failure notifications to %s subs", len(ress))
    return


def _create_message(
        *,
        to_email: str = "",
        msg_subject: str = "",
        msg_text: str = "",
        headers: Dict = {}
) -> Dict:
    lines = msg_text.split("\n")
    email_text = "".join(f"<div>{line}</div>" for line in lines)
    msg_text = f"""<div>{email_text}</div> """
    message = MIMEText(msg_text, "html")
    message['to'] = to_email
    message['from'] = ENV.GMAIL_SEND_ADDR
    message['subject'] = msg_subject
    for key, val in headers.items():
        message.add_header(key, val)
    return {
        "raw": base64.urlsafe_b64encode(
            message.as_bytes()).decode("utf-8"),
    }


def _send_msg(msg: Dict) -> Dict:
    res = (MAIL_SERVICE
           .users()
           .messages().send(
               userId=MAGIC_GMAIL_USER_ID,
               body=msg)).execute()
    return res
