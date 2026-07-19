import time
import inspect
import faulthandler
faulthandler.enable() # Enable faulthandler to get better stack traces on crashes with the inspect module in windows
import os

bcolors = {
    "WARNING": '\033[93m',
    "ERROR": '\033[91m',
    "OUTPUT": '\033[96m',
    "CONFIG": '\033[0;35m',
    "ENDC": '\033[0m',
    "DEBUG": '\033[92m',
    "SUCCESS": '\033[92m',
}

class Logger:
    def __init__(self, log_file = './logging.log', block_logs_from = []):
        print("Creating Logger")
        self.format = '{time} [{location}] [{level}] {message}'
        self.log_file = log_file
        self.block_logs_from = block_logs_from

    def get_message_object(self, *args, level = 'INFO', filepath = None):
        return {
            'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'level': level,
            'location': filepath,
            'message': ' '.join([str(arg) for arg in args])
        }

    def _caller_location(self):
        """File path and line of the code that called the logging method.

        Uses frame walking instead of inspect.stack(): inspect.stack() builds
        source context for every frame, which is slow and can trigger
        third-party lazy-module import machinery mid-log (e.g. speechbrain's
        LazyModule raising ImportError inside logging.error). Must never
        raise — logging is called from except blocks.
        """
        try:
            # _caller_location <- _log <- public method (info/error/...) <- caller
            frame = inspect.currentframe().f_back.f_back.f_back
            filepath = os.path.relpath(frame.f_code.co_filename)
            line = frame.f_lineno
            return filepath, line
        except Exception as e:
            print(f'Error getting caller information: {e}')
            return 'unknown', 0

    def _log(self, level, *args):
        filepath, line = self._caller_location()
        if filepath in self.block_logs_from:
            return
        message = self.get_message_object(*args, level=level, filepath=filepath+":"+str(line))
        self._output(self.format.format(**message), level)

    def _output(self, message: str, level: str):
        message = message.encode('utf-8', errors='replace').decode('utf-8')
        try:
            if level in bcolors:
                print(bcolors[level]+message+bcolors["ENDC"])
            else:
                print(message)
        except UnicodeEncodeError:
            print('Error encoding message')
        try:
            with open(self.log_file, 'a') as f:
                remove_colors = message
                for color in bcolors.values():
                    remove_colors = remove_colors.replace(color, '')
                f.write(remove_colors + '\n')
        except Exception as e:
            print(f'Error writing to log file: {e}')
            # raise e

    def info(self, *args):
        self._log('INFO', *args)

    def output(self, *args):
        self._log('OUTPUT', *args)

    def config(self, *args):
        self._log('CONFIG', *args)

    def error(self, *args):
        self._log('ERROR', *args)

    def warning(self, *args):
        self._log('WARNING', *args)

    def debug(self, *args):
        self._log('DEBUG', *args)

    def success(self, *args):
        self._log('SUCCESS', *args)

    def warn(self, *args):
        self._log('WARNING', *args)

    def out(self, *args):
        self._log('OUTPUT', *args)

logging = Logger() # Create a logger object to be used throughout the program

def getLogger(app_name):
    if app_name == 'werkzeug':
        return None
    return logging
