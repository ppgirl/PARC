__author__ = 'Zhang Shaojun'
# transformed layered controller
# main()

import sys

import hub
hub.patch()

from cfg import LOG
import app_manager

def main():
    try:
        app = app_manager.AppManager()
        app()
    except KeyboardInterrupt:
        LOG.info("tflc: keyboard interrupt, now quit")
        sys.exit(0)

if __name__ == "__main__":
    main()
