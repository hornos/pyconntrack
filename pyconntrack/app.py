
import pprint
import copy
import json
import os
import sys
import re
import argparse
import logging
import logging.handlers
from dotenv import load_dotenv
import asyncio
import signal


class Path:
    '''Wrapper class for filename related functions'''
    def __init__(self, _path):
        assert _path != None
        self.__basename = os.path.basename(_path)
        self.__basestem = os.path.splitext(self.basename)[0]
        self.__dirname = os.getcwd() # os.path.dirname(_path)
        self.__abspath = os.path.abspath(_path)
        self.__absdir = os.path.dirname(os.path.abspath(self.dirname))

    @property
    def basename(self):
        return self.__basename

    @property
    def basestem(self):
        return self.__basestem

    @property
    def dirname(self):
        return self.__dirname

    @property
    def abspath(self):
        return self.__abspath

    @property
    def absdir(self):
        return self.__absdir

    # __init__
# Path

class Config:
    '''Wrapper class for global config'''
    def __init__(self, id="app", mode="cli"):
        self.__id = id
        self.__mode = mode
        self.pid_file_path = None
        self.is_dblogger = False
    # __init__

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, val):
        self.__id = val

    @property
    def mode(self):
        return self.__mode

    @mode.setter
    def mode(self, val):
        if( re.match(r"^[a-zA-Z0-9]+$", val)):
            self.__mode = val
        else:
            raise ValueError( f'Invalid mode: {val}' )
# Config


# Server
class App():
    def __init__(self, script=__file__, id=None, mode=None, description = None):
        self.path = Path(script)
        self.config = Config(id, mode)

        self.load_dotenv()
        self.parse_arguments(description)

        # init_config
        if id is None:
          _id = "app"
          self.config.id = _id

        self.init_logging()
        self.register_signal_handlers()
        self.logger.info(f'Python Version: {sys.version_info.major}.{sys.version_info.minor}')
    # __init__

    def init_pidfile(self, pid_file_name = None):
        # Get and write PID to pidfile
        pid = os.getpid()
        if not pid_file_name:
            pid_file_name = self.config.id # os.path.splitext(self.path.basename)[0]
        pid_file_path = os.path.join(self.path.dirname, f'{pid_file_name}.pid')

        with open(pid_file_path, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))

        self.logger.info(f'PID = {pid}')
        self.logger.debug(f'pidfile = {pid_file_path}')
        self.config.pid = pid
        self.config.pid_file_path = pid_file_path
    # init_pidfile

    def parse_arguments(self, description=None):
        self._arg_parser = argparse.ArgumentParser(description=description)
        self.add_arguments()
        self.arguments = self._arg_parser.parse_args()
    # parse_arguments

    def add_arguments(self):
        '''General arguments'''
        self._arg_parser.add_argument(
            '-d','--debug',
            default=False,
            action='store_true',
            help='Turn on debug logging')

        self._arg_parser.add_argument(
            '-E', '--logfile',
            metavar='LOGFILE',
            help=f'Write logs to LOGFILE')
    # add_arguments

    def init_logging(self):
        # --debug
        self.logger = logging.getLogger(self.path.basename)
        loglevel = logging.INFO
        logformat = f"%(asctime)s %(levelname)-8s %(name)-18s {self.config.id} - %(message)s\r"
        dateformat = "%Y-%m-%dT%H:%M:%S"

        if self.arguments.debug:
            loglevel = logging.DEBUG
            # logformat = f"%(asctime)s %(levelname)-8s %(name)-18s %(module)-16s {self.config.id} - %(message)s\r"
            self.logger.debug('Debug logging turned on')

        logging.basicConfig( level=loglevel, format=logformat, datefmt=dateformat )

        # --logfile <log>
        if self.arguments.logfile:
            global_logger = logging.getLogger()
            global_stdout = global_logger.handlers[0]
            logfile = os.path.join(f'{self.arguments.logfile}')
            handler = logging.handlers.RotatingFileHandler(logfile,maxBytes=2000000) # 2MB
            handler.setLevel(loglevel)
            formatter = logging.Formatter( logformat, datefmt=dateformat)
            handler.setFormatter(formatter)
            global_logger = logging.getLogger()
            global_logger.addHandler(handler)
            self.logger.info(f'Logfile: {self.arguments.logfile}')
            if self.arguments.silent:
                global_logger.removeHandler(global_stdout)
        # logfile
    # init_logging

    def load_dotenv(self):
        self.dotenv_file_path = os.environ.get('DOTENV') or os.path.join(self.path.dirname, ".env")
        load_dotenv(dotenv_path=self.dotenv_file_path)
    # load_dotenv

    def register_signal_handlers(self):
        signal.signal(signal.SIGTERM, self.signal_handler_sigterm)
        signal.signal(signal.SIGINT, self.signal_handler_sigterm)
    # register_signal_handlers

    def start_noshell(self):
        self.init_logging()
        self.start_asyncio_task_loop()
    # start_noshell

    def start(self):
        return self.start_noshell()
    # start

#
# TASKS
#

    def signal_handler_sigterm(self, signum, stack):
        self.logger.debug(f'Signal received: {signum}')
        if signum == signal.SIGTERM or signum == signal.SIGINT:
            self.logger.info(f'Application terminated')
            if self.config.pid_file_path:
                os.remove( self.config.pid_file_path )
            sys.exit(1)
    # def


    def start_asyncio_task_loop(self):

        loop = asyncio.get_event_loop()
        loop.set_debug(self.arguments.debug)
        signals = (signal.SIGTERM, signal.SIGINT)

        # Signal handlers
        for s in signals:
            loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task( self.task_loop_shutdown(s, loop) ) )
        # exceptions
        # loop.set_exception_handler(self.loop_exception_handler)

        try:
            self.create_asyncio_tasks()
            loop.run_forever()
        except Exception as exc:
            raise exc
        finally:
            loop.close()
            # if self.config.pid_file_path:
            #     os.remove( self.config.pid_file_path )
            self.logger.debug( 'Task loop closed' )
            self.signal_handler_sigterm(self._signal, None)
    # start_asyincio_task_loop

    def create_asyncio_tasks(self):
        loop = asyncio.get_event_loop()
        return loop
    # create_tasks

    async def task_loop_shutdown(self, signal, loop):
        """Cleanup tasks tied to the service's shutdown."""

        self._signal = signal

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        self.logger.debug(f'Cancelling {len(tasks)} outstanding tasks')
        [task.cancel() for task in tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        self.logger.debug(f'Finished awaiting cancelled tasks, results: {results}')
        loop.stop()
    # task_loop_shutdown

    # if the connection terminates eg. nmap port scan, catch here
    def loop_exception_handler(self, loop, exc):
        # self.logger.warning('Abnormal connection close (Port scan?)')
        self.logger.exception(exc)
        # print(loop.__dict__)
    # loop_exception_handler

    async def asyncio_task_mark(self, timeout = 3000):
        # TODO: os.environ['MARK_TIMEOUT']
        logger = logging.getLogger('mark')

        try:
          await asyncio.sleep(timeout)
          while True:
              logger.info("-- MARK --")
              await asyncio.sleep(timeout)
        except asyncio.CancelledError:
            logger.info("Task mark cancelled")
    # async_task_mark

    async def asyncio_task_sleep(self, sleep=50, name="sleep"):
        logger = logging.getLogger('sleep')
        logger.info("%s start" % name)
        try:
            await asyncio.sleep(sleep)
        except asyncio.CancelledError:
            logger.info("Task %s cancelled" % name)
        logger.info("%s done" % name)
    # async_task_sleep
