import logging

config = {
   "logger": logging.getLogger("audit"),
   "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
   "log_level": logging.INFO,
   # "log_file": "audit.log"  # Specify the log file path
}

