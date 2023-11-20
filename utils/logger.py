from datetime import datetime

class Logger:
    def __init__(self):
        self.red = "\033[91m"
        self.yellow = "\033[93m"
        self.green = "\033[92m"
        self.grey = "\033[90m"
        self.reset = "\033[37m"

    def fetch_time(self):
        time = datetime.now().strftime("%H:%M:%S")
        return f"[{time}]"

    def info(self, text):
        current_time = self.fetch_time()
        print(f"{current_time} {self.grey}[~]{self.reset} {text}")

    def error(self, text):
        current_time = self.fetch_time()
        print(f"{current_time} {self.red}[-]{self.reset} {text}")

    def warning(self, text):
        current_time = self.fetch_time()
        print(f"{current_time} {self.yellow}[!]{self.reset} {text}")

    def success(self, text):
        current_time = self.fetch_time()
        print(f"{current_time} {self.green}[+]{self.reset} {text}")

log = Logger()
