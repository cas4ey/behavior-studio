# coding=utf-8
#!/usr/bin/env python
# -----------------
# file      : main.py
# date      : 2012/09/15
# author    : Victor Zarubkin
# contact   : victor.zarubkin@gmail.com
# copyright : Copyright (C) 2012  Victor Zarubkin
# license   : This file is part of BehaviorStudio.
#           :
#           : BehaviorStudio is free software: you can redistribute it and/or modify
#           : it under the terms of the GNU General Public License as published by
#           : the Free Software Foundation, either version 3 of the License, or
#           : (at your option) any later version.
#           :
#           : BehaviorStudio is distributed in the hope that it will be useful,
#           : but WITHOUT ANY WARRANTY; without even the implied warranty of
#           : MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#           : GNU General Public License for more details.
#           :
#           : You should have received a copy of the GNU General Public License
#           : along with BehaviorStudio. If not, see <http://www.gnu.org/licenses/>.
#           :
#           : A copy of the GNU General Public License can be found in file COPYING.
############################################################################

""" Main editor's script file.

Launch it to run the application.
"""

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2012  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

import os
import sys
import getopt
import socket

from time import sleep
from xml.dom.minidom import parse

from PySide.QtCore import *
from PySide.QtGui import *

from application_palette import setPalette
from auxtypes import absPath, toUnixPath, joinPath

import globals


def _readConfigIcons(configFile, configData):
    iconsPath = ''
    if configData.hasAttribute('icons'):
        path = configData.getAttribute('icons')
        path = absPath(path, configFile, True)
        if path is None or len(path) < 1 or not os.path.exists(path):
            print(u'warning: icons path \"{0}\" does not exist!'.format(path))
            print('')
        else:
            iconsPath = path
    else:
        print(u'warning: Config file \"{0}\" have no icons path! (attribute \"<config icons=""/>\")'.format(configFile))
        print('')
        return

    if not iconsPath:
        print('warning: no icons will be loaded for application!')
        print('')
        return

    globals.applicationIconsPath = iconsPath


def _readConfig(args):
    settings = QSettings('Victor Zarubkin', 'Behavior Studio')

    if socket.gethostname().lower() == 'victor':
        settings.beginGroup('startup')
        value = settings.value('showLogo')
        if value is not None:
            value = value.lower()
            if value in ('true', 'false'):
                globals.showLogo = value == 'true'
        settings.endGroup()
    else:
        globals.showLogo = True

    currDir = os.getcwd()  # os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

    # Reading application config file:
    configFile = None
    data = None

    try_configs = []
    if isinstance(args.config_file, list):
        try_configs = args.config_file
    else:
        try_configs.append(args.config_file)

    okay = False
    err = False
    for conf in try_configs:
        configFile = conf
        data = None

        if not os.path.isabs(configFile):
            configFile = absPath(configFile, currDir)  # make full path from relative path
        else:
            configFile = toUnixPath(configFile)

        if configFile is None:
            err = True
            print(u'warning: Config file \"{0}\" does not exist!'.format(conf))
            continue

        if not os.path.exists(configFile):
            err = True
            print(u'warning: Config file \"{0}\" does not exist!'.format(configFile))
            continue

        dom = parse(configFile)
        data = dom.getElementsByTagName('config')
        if not data:
            err = True
            print(u'warning: Config file \"{0}\" is wrong formatted! It must have header \"<config>\".'
                  .format(configFile))
            continue

        okay = True
        break

    if not okay:
        print('error: Can\'t load application configuration!')
        print('')
        return False

    if err:
        print('')

    _readConfigIcons(configFile, data[0])
    return True


def _checkPackages():
    eng_package_error_message = u''
    rus_package_error_message = u''

    # -------------------------------------------------
    # 'lxml' package is required!
    # trying to find it...
    try:
        import lxml
    except ImportError:
        eng_message = u'<font color=\"red\">- <b>\'lxml\'</b></font>, which can be downloaded from \
            <a href=\"http://pypi.python.org/pypi/lxml/\" style=\"color: CornflowerBlue\">here</a>;'

        eng_message += u'<br/><u>installation:</u><br/>'
        eng_message += u'simply download and run an \".exe\"-file.'

        rus_message = u'<font color=\"red\">- <b>\'lxml\'</b></font>, которая может быть скачана \
            <a href=\"http://pypi.python.org/pypi/lxml/\" style=\"color: CornflowerBlue\">отсюда</a>;'

        rus_message += u'<br/><u>установка:</u><br/>'
        rus_message += u'просто скачайте и запустите \".exe\"-файл.'

        if eng_package_error_message:
            eng_package_error_message += u'<br/><br/>'
        eng_package_error_message += eng_message

        if rus_package_error_message:
            rus_package_error_message += u'<br/><br/>'
        rus_package_error_message += rus_message

    # 'lxml' found, ok!

    # -------------------------------------------------
    # 'sortedcontainers' package is required!
    # trying to find it...
    try:
        import sortedcontainers
    except ImportError:
        eng_message = u'<font color=\"red\">- <b>\'sortedcontainers\'</b></font>, which can be downloaded from ' \
                      u'<a href=\"http://pypi.python.org/pypi/sortedcontainers/\" style=\"color: CornflowerBlue\">' \
                      u'here</a>;'

        eng_message += u'<br/><u>installation:</u><br/>'
        eng_message += u'1. install <a href=\"http://pip.pypa.io/en/latest/installing.html#install-pip\" ' \
                       u'style=\"color: CornflowerBlue\">pip</a>;<br/>'
        eng_message += u'2. run \"pip install sortedcontainers\" from system command line (e.g., \"cmd\" on Windows).'

        rus_message = u'<font color=\"red\">- <b>\'sortedcontainers\'</b></font>, которая может быть скачана ' \
                      u'<a href=\"http://pypi.python.org/pypi/sortedcontainers/\" style=\"color: CornflowerBlue\">' \
                      u'отсюда</a>;'

        rus_message += u'<br/><u>установка:</u><br/>'
        rus_message += u'1. установить <a href=\"http://pip.pypa.io/en/latest/installing.html#install-pip\" ' \
                       u'style=\"color: CornflowerBlue\">pip</a>;<br/>'
        rus_message += u'2. выполнить команду \"pip install sortedcontainers\" в системной командной строке ' \
                       u'(например, \"cmd\" для Windows).'

        if eng_package_error_message:
            eng_package_error_message += u'<br/><br/>'
        eng_package_error_message += eng_message

        if rus_package_error_message:
            rus_package_error_message += u'<br/><br/>'
        rus_package_error_message += rus_message

    # 'sortedcontainers' found, ok!

    return eng_package_error_message, rus_package_error_message


def main(argv):
    # Create a Qt application
    app = QApplication(argv)
    app.setStyle('macintosh')
    setPalette(app)

    eng_package_error_message, rus_package_error_message = _checkPackages()

    if eng_package_error_message or rus_package_error_message:
        error_message = u'<font color=\"red\">Next python packages are required for running the program:</font><br/>'
        error_message += eng_package_error_message
        error_message += u'<br/><font color=\"yellow\">---------------------------------' \
                         u'-------------------------------------------------</font><br/>'
        error_message += u'<font color=\"red\">Для запуска программы необходимы следующие библиотеки для python:' \
                         u'</font><br/>'
        error_message += rus_package_error_message
        mb = QMessageBox(QMessageBox.Critical, 'Package Error', error_message, QMessageBox.Ok)
        mb.exec_()
        sys.exit()

    from main_window import AppArgs, MainWindow

    # Read input args
    appArgs = AppArgs(argv)
    opts = None
    try:
        opts, args = getopt.getopt(argv[1:], 'hdc:', ['help', 'debug', 'config=', 'config-file='])
    except getopt.GetoptError:
        appArgs.options_error = True
        mb = QMessageBox(QMessageBox.Warning, 'Options Error',
                         '<font color=\"red\">There are some options error!<br/>Read studio output...</font>',
                         QMessageBox.Ok)
        mb.exec_()

    if not appArgs.options_error:
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                infoString = 'available options:<br/>\
                -h, --help - see this hint<br/>\
                -c, --config, --config-file - set start configuration file<br/>'
                infoString += '<br/>Example:<br/><b>{0} -c config.xml</b>'.format(appArgs.current_file)
                mb = QMessageBox(QMessageBox.Information, 'Options Help', infoString, QMessageBox.Ok)
                mb.exec_()
                sys.exit()
            elif opt in ('-c', '--config', '--config-file'):
                appArgs.config_file = arg
                appArgs.config_file_default = False
            elif opt in ('-d', '--debug'):
                appArgs.debug = True

    if len(args)>0:
        appArgs.project_for_opening = args[0]

    if not _readConfig(appArgs):  # read icons path
        mb = QMessageBox(QMessageBox.Critical, 'Configuration Error',
                         'Can\'t load application configuration!<br/>'
                         'Configuration file <b>\'{0}\'</b> does not exist.'.format(appArgs.config_file),
                         QMessageBox.Ok)
        mb.exec_()
        sys.exit()

    if globals.showLogo:
        splash = QSplashScreen(QPixmap(joinPath(globals.applicationIconsPath, 'splash2.png')))
        splash.showMessage('<h2>Behavior Studio {0}</h2>'.format(globals.strVersion), Qt.AlignHCenter, Qt.red)
        splash.show()
        sleep(3)
    else:
        splash = None

    # Create main window
    window = MainWindow(appArgs)
    window.show()

    if splash is not None:
        splash.finish(window)
    # window = main_window.MainStackedWindow()
    # window.hide()

    # Enter Qt application main loop
    app.exec_()
    sys.exit()

if __name__ == '__main__':
    main(sys.argv)
