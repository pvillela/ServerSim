"""
From https://stackoverflow.com/questions/2557168/how-do-i-change-the-default-format-of-log-messages-in-python-app-engine
"""

import logging


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    )

logging.info('Danger Will Robinson!')
# 03-31 20:00 root         INFO     Danger Will Robinson!
root = logging.getLogger()
hdlr = root.handlers[0]
fmt = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
hdlr.setFormatter(fmt)
logging.info('Danger Will Robinson!')
# root        : INFO     Danger Will Robinson!
