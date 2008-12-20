# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Marco Dinacci <dev@dinointeractive.com> 
# All rights reserved.

"""
This module simplify the usage of the 
standard Python logging module.
"""

import logging
# insert into this module namespace the logging levels
from logging import CRITICAL,FATAL,ERROR,WARNING,INFO,DEBUG

class Logger(object):
	"""
	Base class for loggers.
	Although it is concrete, it is not intended to be used directly but
	rather through subclasses.
	
	FIXME: when creating loggers with the same name, log statements
	are logged multiple times and new logger objects are created (that's weird...)
	"""
	def __init__(self, loggerName, handler, logLevel):
		self._logger = logging.getLogger(loggerName)
		self._logger.addHandler(handler)
		self._logger.setLevel(logLevel)

	def __getattribute__(self, key):
		attr = None
		try:
			attr = object.__getattribute__(self, key)
		except AttributeError:
			attrObj = object.__getattribute__(self, "_logger")
			attr = getattr(attrObj, key)
		return attr
	
class ConsoleLogger(Logger):
	"""
	Logger to console.
	"""
	def __init__(self, loggerName="consolelogger", logLevel=logging.INFO):
		handler = logging.StreamHandler()
		formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
		handler.setFormatter(formatter)
		super(ConsoleLogger,self).__init__(loggerName, handler, logLevel)

class FileLogger(Logger):
	"""
	Logger to file.
	"""
	def __init__(self, logFileName, loggerName="filelogger", logLevel=logging.INFO):
		handler = logging.FileHandler(logFileName)
		formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
		handler.setFormatter(formatter)
		super(FileLogger, self).__init__(loggerName, handler, logLevel)

