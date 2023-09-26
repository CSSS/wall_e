import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Gmail:

    def __init__(self, logger, config, smtp='smtp.gmail.com', port=587, max_number_of_retries=5):
        """
        initialized the gmail object for a gmail account

        :param logger: the service's logger instance
        :param config: used to determine the gmail credentials
        :param smtp: the server that hosts the smptlib server for gmail
        :param port: the port for the smptlib server for gmail
        :param max_number_of_retries: the maximum number of times to try opening and closing the connection
         to the smptlib server as well as sending the email
        """
        self.logger = logger
        self._connection_successful = False
        number_of_retries = 0
        self.from_email = config.get_config_value("gmail", "username")
        self.password = config.get_config_value("gmail", "password")
        self.max_number_of_retries = max_number_of_retries
        self._enabled = self.from_email != "NONE" and self.password != "NONE"
        if self._enabled:
            while not self._connection_successful and number_of_retries < max_number_of_retries:
                try:
                    self.server = smtplib.SMTP(f'{smtp}:{port}')
                    self.logger.info(f"[Gmail __init__()] setup smptlib server connection to {smtp}:{port}")
                    self.server.connect(f'{smtp}:{port}')
                    self.logger.info("[Gmail __init__()] smptlib server connected")
                    self.server.ehlo()
                    self.logger.info("[Gmail __init__()] smptlib server ehlo() successful")
                    self.server.starttls()
                    self.logger.info("[Gmail __init__()] smptlib server ttls started")
                    self.logger.info(f"[Gmail __init__()] Logging into account {self.from_email}")
                    self.server.login(self.from_email, self.password)
                    self.logger.info(f"[Gmail __init__()] login to email {self.from_email} successful")
                    self._connection_successful = True
                    self.error_message = None
                except Exception as e:
                    number_of_retries += 1
                    self.logger.error(f"[Gmail __init__()] experienced following error when initializing.\n{e}")
                    self.error_message = f"{e}"

    def send_email(self, subject, body, to_email, to_name, from_name="WALL-E", attachment=None):
        """
        send email to the specified email address

        Keyword Argument
        subject -- the subject for the email to send
        body - -the body of the email to send
        to_email -- the email address to send the email to
        to_name -- the name of the person to send the email to
        from_name -- the name to assign to the from name field
        attachment -- the logs to attach to the email if applicable

        Return
        Bool -- true or false to indicate if email was sent successfully
        error_message -- None if success, otherwise, returns the error experienced
        """
        if not self._enabled:
            return True, None
        if self._connection_successful:
            number_of_retries = 0
            while number_of_retries < self.max_number_of_retries:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = from_name + " <" + self.from_email + ">"
                    msg['To'] = to_name + " <" + to_email + ">"
                    msg['Subject'] = subject
                    msg.attach(MIMEText(body))

                    if attachment is not None:
                        try:
                            package = open(attachment, 'rb')
                            payload = MIMEBase('application', 'octet-stream')
                            payload.set_payload(package.read())
                            encoders.encode_base64(payload)
                            payload.add_header('Content-Disposition', f"attachment; filename={attachment}")
                            msg.attach(payload)
                            self.logger.info(f"{attachment} has been attached")
                        except Exception as e:
                            self.logger.info(f"{attachment} could not be attached. Error: {e}")

                    self.logger.info(f"[Gmail send_email()] sending email to {to_email}")
                    self.server.send_message(from_addr=self.from_email, to_addrs=to_email, msg=msg)
                    return True, None
                except Exception as e:
                    self.logger.info(f"[Gmail send_email()] unable to send email to {to_email} due to error.\n{e}")
                    number_of_retries += 1
                    self.error_message = f"{e}"
        return False, self.error_message

    def successful_connection(self):
        if self._enabled:
            return True, None
        return self._connection_successful, self.error_message

    def close_connection(self):
        """
        Closes connection to smptlib server

        Return
        Bool -- true or false to indicate if email was sent successfully
        error_message -- None if success, otherwise, returns the error experienced
        """
        if not self._enabled:
            return True, None
        if self._connection_successful:
            number_of_retries = 0
            while number_of_retries < self.max_number_of_retries:
                try:
                    self.logger.info("[Gmail close_connection()] closing connection to smtplib server")
                    self.server.close()
                    self.logger.info("[Gmail close_connection()] connection to smtplib server closed")
                    return True, None
                except Exception as e:
                    self.logger.error(
                        "[Gmail close_connection()] experienced following error when attempting "
                        f"to close connection to smtplib server.\n{e}"
                    )
                    number_of_retries += 1
                    self.error_message = f"{e}"
        return False, self.error_message
