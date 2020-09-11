import os
import logging

from app.app import App

CONFIG_FILE = os.getenv('CONFIG_FILE', 'config.ini')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')


def run():
    logging.basicConfig(level=LOG_LEVEL)

    app = App(CONFIG_FILE)
    app.init()
    app.run()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run()
