import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def rotation_filename(self, default_name):
    
        base, ext = os.path.splitext(self.baseFilename)
        timestamp = datetime.now().strftime("%Y_%m_%d__%H.%M")
        return f"{base}_{timestamp}.log"
