# -*- coding: utf-8 -*-
# Copyright (C) 2014 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
__author__ = 'Daniele'

import os
import sys
import logging
import logging.handlers

import api

def log_setup(base_path, base_name):
    # check base path
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    # set up logging to file

    root = logging.getLogger('')

    # set the level of the root logger
    root.setLevel(logging.DEBUG)

    # define the file formatter
    file_fmt = logging.Formatter('%(asctime)s %(name)-12s ' +
                                 '%(levelname)-8s %(message)s')

    # define log rotation
    rotation = logging.handlers.TimedRotatingFileHandler(
                filename=os.path.join(base_path, base_name),
                when='midnight',
                backupCount = 15)

    # console logging
    console = logging.StreamHandler()


    # assign formatter to the handlers
    console .setFormatter(file_fmt)
    rotation.setFormatter(file_fmt)

    # add the handlers to the root logger
    logging.getLogger('').addHandler(rotation)

    if not hasattr(sys, "frozen"):
        logging.getLogger('').addHandler(console )

log_path = api.get_user_data_path('logs')
log_setup(log_path, 'l5rcm.log')

app = logging.getLogger('app')
ui = logging.getLogger('ui')
model = logging.getLogger('model')
api = logging.getLogger('api')
rules = logging.getLogger('rules')
