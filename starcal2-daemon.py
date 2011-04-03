#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# 
# Copyright (C) 2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License,    or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Or on Debian systems, from /usr/share/common-licenses/GPL

import sys, os
from os import listdir, makedirs
from os.path import join, isfile, isdir, exists
from time import time, localtime, sleep
from subprocess import Popen, PIPE

import logging
import logging.config

from gobject import timeout_add_seconds
import glib
from glib import MainLoop

from paths import *

from scal2.cal_modules import to_jd, DATE_GREG
from scal2 import event_man
from scal2.event_man import eventsDir

logging.config.fileConfig(join(rootDir, 'logging-system.conf'))
log = logging.getLogger('daemon')## FIXME

########################## Global Variables #########################

uidList = [1000] ## FIXME
uiName = 'gtk'
notifyCmd = [join(rootDir, 'run'), join('ui_'+uiName, 'event_notify.py')]
pidFile = '/var/run/starcal2d.pid'
pid = os.getpid()

open(pidFile, 'w').write(str(pid))

events = event_man.loadEvents()

########################## Functions #################################

def assertDir(path):
    if not exists(path):
        makedirs(path)
    elif not isdir(path):
        raise IOError('%r must be a directory'%path)

def notify(eid):
    #log.debug('notify eid %s'%eid)
    for uid in uidList:
        Popen(notifyCmd+[str(eid), str(uid)], stdout=PIPE)

def prepareToday():
    tm = time()
    (y, m, d) = localtime(tm)[:3]
    #log.debug('Date: %s/%s/%s   Epoch: %s'%(y, m, d, tm))
    todayJd = to_jd(y, m, d, DATE_GREG)
    dayRemainSecondsCeil = int(-(tm - 1)%(24*3600))
    timeout_add_seconds(dayRemainSecondsCeil, prepareToday)
    for event in events:
        if not event.enable:
            continue
        if not event.notifiers:
            continue
        eid = event.eid
        occur = event.calcOccurrenceForJdRange(todayJd, todayJd+1)
        #addList = []
        for (start, end) in occur.getTimeRangeList():
            if start >= tm:
                timeout_add_seconds(int(start-tm)+1, notify, eid)
                #log.debug(str(int(start-tm)+1))
                #addList.append(int(start-tm)+1)
            #log.debug('start=%s, tm=%s, start-tm=%s'%(start, tm, start-tm))
    #addList.sort()
    #log.debug('addList=%r'%addList[:20])

########################## Starting Program ###########################

prepareToday()
MainLoop().run()
#log.debug('starcal2-daemon: exiting')
os.remove(pidFile)
