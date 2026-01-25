import logging
import logging.handlers
import socket
import os
import json

class dLogs:
    """
    The 1-click logger. 
    Connects to your local dLogs stack automatically.
    """
    def __init__(self, app_name):
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.INFO)
        
        # Ensure log directory exists
        log_dir = "C:/Logs"
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError:
                pass # Handle permission errors or race conditions gracefully
        
        # 1. Connect to Local Loki (via SysLog/Promtail bridge)
        # Or simple rotating file that Promtail watches
        try:
            handler = logging.handlers.RotatingFileHandler(
                f"{log_dir}/{app_name}.json", maxBytes=5*1024*1024, backupCount=2
            )
            
            # 2. JSON Format (Best for Loki)
            # Custom formatter to create valid JSON lines
            class JsonFormatter(logging.Formatter):
                def format(self, record):
                    log_record = {
                        "time": self.formatTime(record, self.datefmt),
                        "app": app_name,
                        "level": record.levelname,
                        "msg": record.getMessage()
                    }
                    return json.dumps(log_record)

            formatter = JsonFormatter(datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        except Exception as e:
            print(f"dLogs Warning: Could not setup file logging: {e}")

    def log(self, msg):
        self.logger.info(msg)
        
    def alert(self, msg):
        self.logger.error(msg)
        # Optional: Trigger ntfy immediately for errors
        # requests.post("http://localhost:8080/my_topic", data=msg)
