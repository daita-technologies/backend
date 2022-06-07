import os
import logging
import datetime as dt
import logging.handlers as Handlers

loggingDir = "../../log"
# set up logger
def setupLogger(name, level=logging.DEBUG):
    def filer(self):
        now = dt.datetime.now()
        return os.path.join(loggingDir, name + "_" + now.strftime("%Y-%m-%d") + ".log")

    formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s - %(message)s")
    logger = logging.getLogger(name)
    logger.setLevel(level=level)
    logHandler = Handlers.TimedRotatingFileHandler(
        filename=os.path.join(loggingDir, name + ".log"),
        when="S",
        interval=86400,
        backupCount=1,
    )
    logHandler.rotation_filename = filer
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    logger.addHandler(logHandler)


setupLogger("debug")
setupLogger("error")
setupLogger("info")
logDebug = logging.getLogger("debug")
logInfo = logging.getLogger("info")
logError = logging.getLogger("error")
