import logging

'''
logger = logging.getLogger("testName")
logging.basicConfig(filename='loggingTest.log', encoding='utf-8', level=logging.DEBUG)



logger.debug('This message should go to the log file')
logger.info('So should this')
logger.warning('And this, too')
logger.error('And non-ASCII stuff, too, like Øresund and Malmö')
'''

# Set up a logger for session updates
session_logger = logging.getLogger("session_logger")
logging.basicConfig(filename='session_updates.log', encoding='utf-8', level=logging.DEBUG)
#session_logger.setLevel(logging.INFO)
#logging.basicConfig(filename='session_updates.log', encoding='utf-8', level=logging.INFO)
session_logger.info('test 5')
test=input("type anything")


