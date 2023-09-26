from utilities.Gmail import Gmail


def send_email_alert_about_error(logger, config, message, file_path):
    """

    :param logger: the service's logger instance
    :param config: used to determine the gmail credentials
    :param message: the message that needs to be emailed to the bot managers
    :param file_path: the path for the file that contains the error
    :return:
    """
    gmail = Gmail(logger, config)
    if not gmail.connection_successful:
        return False, gmail.error_message
    success, error_message = gmail.send_email(
        "WALL_E error", message, "csss-bot-manager@sfu.ca", "CSSS Bot Manager", from_name="WALL-E",
        attachment=file_path
    )
    if not success:
        return False, error_message
    return gmail.close_connection()
