import logging

class Logger():

    BUILDING_BRICKS = 'Building Renko Bricks'
    WAITING_SIGNAL = 'Looking for a Signal... please wait'
    SIGNAL_FOUND = 'Signal Found'
    STOP_LOSS_TRIGGERED = 'Stop Loss Triggered'
    STOP_LOSS_STATUS = 'Stop Loss Status:'
    MANUAL_EXIT_TRIGGERED = 'Manual Exit Triggered'
    GETTIN_BEST_PRICE = 'Trying to get best price'
    MONITORING_POSITION = 'Monitoring Position:'
    UPDATING_SL = 'Updating Stop Loss Order'
    SL_UPDATED = 'Stop Loss Order Updated:'
    
    def __init__(self):
        logging.basicConfig(filename="./std.log", format='%(asctime)s %(message)s', filemode='w')
        self.log: Logger = logging.getLogger()
        self.log.setLevel(logging.DEBUG)

    
    def info(self, msg):
        self.log.info(msg)
        print(msg)
    
    def error(self, msg):
        self.log.error(msg)
        print(msg)
    
    def debug(self, msg):
        self.log.debug(msg)
        print(msg)
    
    def warning(self, msg):
        self.log.warning(msg)
        print(msg)
    
    def critical(self, msg):
        self.log.critical(msg)
        print(msg)
    
    def exception(self, msg):
        self.log.exception(msg)
        print(msg)
    
    def log(self, msg):
        self.log.log(msg)
        print(msg)