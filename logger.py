import logging

class Logger():
    
    def __init__(self):
        logging.basicConfig(filename="./std.log", format='%(asctime)s %(message)s', filemode='w')
        self.log = logging.getLogger()
        self.log.setLevel(logging.DEBUG)