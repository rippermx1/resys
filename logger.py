import logging

class Logger():
    
    def __init__():
        logging.basicConfig(filename="./std.log", format='%(asctime)s %(message)s', filemode='w')
        logger=logging.getLogger()
        logger.setLevel(logging.DEBUG)