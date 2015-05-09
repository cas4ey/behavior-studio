# coding=utf-8
# -----------------
# file      : application_palette.py
# date      : 2014/09/06
# author    : Victor Zarubkin
# contact   : victor.zarubkin@gmail.com
# copyright : Copyright (C) 2014  Victor Zarubkin
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

""" This script file contains application's default style sheets that defines it's appearance. """

__author__ = 'Victor Zarubkin'
__copyright__ = 'Copyright (C) 2014  Victor Zarubkin'
__credits__ = ['Victor Zarubkin']
__license__ = ['GPLv3']
__version__ = '1.3.0'  # this is last application version when this script file was changed
__email__ = 'victor.zarubkin@gmail.com'
############################################################################

from PySide.QtGui import *

#######################################################################################################################
#######################################################################################################################


def _rgb(*args, **kwargs):
    nargs = len(args)
    r = kwargs.get('r', args[0] if nargs > 0 else 0)
    g = kwargs.get('g', args[1] if nargs > 1 else r)
    b = kwargs.get('b', args[2] if nargs > 2 else g)
    a = kwargs.get('a', args[3] if nargs > 3 else 255)
    return 'rgba({0}, {1}, {2}, {3})'.format(r, g, b, a) if a < 255 else 'rgb({0}, {1}, {2})'.format(r, g, b)


def _rgbt(*args, **kwargs):
    nargs = len(args)
    r = kwargs.get('r', args[0] if nargs > 0 else 0)
    g = kwargs.get('g', args[1] if nargs > 1 else r)
    b = kwargs.get('b', args[2] if nargs > 2 else g)
    a = kwargs.get('a', args[3] if nargs > 3 else 255)
    return (QColor(r, g, b, a), _rgb(r, g, b, a)) if a < 255 else (QColor(r, g, b), _rgb(r, g, b))


#######################################################################################################################
#######################################################################################################################


class _ApplicationColors(object):
    def __init__(self):
        self.__colors = {
            QPalette.Window: _rgbt(40, 43, 45),
            QPalette.Base: _rgbt(60, 63, 65),
            QPalette.AlternateBase: _rgbt(55, 58, 60),
            QPalette.Text: _rgbt(204, 207, 209),
            QPalette.WindowText: _rgbt(204, 207, 209),
            QPalette.BrightText: _rgbt(255),
            QPalette.ButtonText: _rgbt(43),
            QPalette.Button: _rgbt(80, 83, 85),
            QPalette.Midlight: _rgbt(110, 113, 115),
            QPalette.Light: _rgbt(132, 135, 137),
            QPalette.Mid: _rgbt(55, 58, 60),
            QPalette.Dark: _rgbt(22, 25, 27)
        }

    def __getitem__(self, item):
        if item in self.__colors:
            return self.__colors[item]
        return _rgbt(0)

    def color(self, role):
        return self.__getitem__(role)

    def setColor(self, role, color):
        r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()
        self.__colors[role] = (color, 'rgba({0}, {1}, {2}, {3})'.format(r, g, b, a)) if a < 255 \
            else (color, 'rgb({0}, {1}, {2})'.format(r, g, b))

    def setColorString(self, role, colorStr):
        col = colorStr.replace('(', '')
        col = col.replace(')', '')
        if 'rgba' in col:
            col = col.replace('rgba', '')
            colors = col.split(',')
            if len(colors) < 4:
                return
            r, g, b, a = int(colors[0].replace(' ', '')), int(colors[1].replace(' ', '')), int(
                colors[2].replace(' ', '')), int(colors[3].replace(' ', ''))
        elif 'rgb' in col:
            col = col.replace('rgb', '')
            colors = col.split(',')
            if len(colors) < 3:
                return
            r, g, b = int(colors[0].replace(' ', '')), int(colors[1].replace(' ', '')), int(colors[2].replace(' ', ''))
            a = int(255)
        else:
            return
        self.__colors[role] = (QColor(r, g, b, a), colorStr)

global_colors = _ApplicationColors()

#######################################################################################################################
#######################################################################################################################


def setPalette(application):
    setApplicationPalette(application)
    setDefaultStyleSheet(application)

#######################################################################################################################
#######################################################################################################################


def setApplicationPalette(application):
    """
    Set Global application palette
    """

    palette = application.palette()

    palette.setColor(QPalette.Window, global_colors[QPalette.Window][0])
    palette.setColor(QPalette.Base, global_colors[QPalette.Base][0])
    palette.setColor(QPalette.AlternateBase, global_colors[QPalette.AlternateBase][0])
    palette.setColor(QPalette.Text, global_colors[QPalette.Text][0])
    palette.setColor(QPalette.WindowText, global_colors[QPalette.WindowText][0])
    palette.setColor(QPalette.BrightText, global_colors[QPalette.BrightText][0])
    palette.setColor(QPalette.ButtonText, global_colors[QPalette.ButtonText][0])

    palette.setColor(QPalette.Button, global_colors[QPalette.Button][0])
    palette.setColor(QPalette.Midlight, global_colors[QPalette.Midlight][0])
    palette.setColor(QPalette.Light, global_colors[QPalette.Light][0])
    palette.setColor(QPalette.Dark, global_colors[QPalette.Dark][0])
    palette.setColor(QPalette.Mid, global_colors[QPalette.Mid][0])

    application.setPalette(palette)

#######################################################################################################################
#######################################################################################################################


def setDefaultStyleSheet(application):
    """
    Set application view by using css
    """

    definition_table = {
        '@text-color@': 'palette(text)',
        '@bright-text-color@': 'palette(bright-text)',
        '@midlight-text-color@': _rgb(224, 227, 229),
        '@mid-text-color@': _rgb(132, 135, 137),
        '@dark-text-color@': _rgb(110, 113, 115),
        '@window-color@': 'palette(window)',
        '@light-window-color@': _rgb(60, 63, 65),
        '@dark-window-color@': _rgb(40, 43, 45),
        '@dark@': _rgb(30, 33, 35),
        '@background-color@': 'palette(base)',
        '@light-background-color@': _rgb(80, 83, 85),
        '@alternate-light-background-color@': _rgb(90, 93, 95),
        '@alternate-background-color@': _rgb(50, 53, 55),
        '@scene-color@': _rgb(43),
        '@decorated-color-args@': '220, 161, 0',
        '@decorated-color@': 'rgb(@decorated-color-args@)',
        '@active-decorated-color-args@': '255, 176, 0',
        '@active-decorated-color@': 'rgb(@active-decorated-color-args@)',
        '@hover-tab-border@': _rgb(144, 147, 149),
        '@line-edit-background@': '@alternate-light-background-color@',
        '@line-edit-background-disabled@': '@dark@',
        '@combobox-background@': '@alternate-light-background-color@',
        '@dock-color@': _rgb(37, 40, 42),
        '@message-box-color@': _rgb(50, 53, 55),
        '@widget-border@': '1px outset @dark@'
    }

    for d in definition_table:
        ok = False
        while not ok:
            v = definition_table[d]
            if v in definition_table:
                definition_table[d] = definition_table[v]
            else:
                ok = True

    styleSheet = application.styleSheet()

    # QListWidget style
    styleSheet += '''
        QListWidget {
            border: @widget-border@;
            border-radius: 4px;
            color: @text-color@;
            background-color: @background-color@;
        }

        QTextEdit {
            border-width: 1px;
            border-style: outset;
            border-color: @dark@;
            border-radius: 4px;
            color: @text-color@;
            background-color: @background-color@;
        }
    '''

    # QDockWidget style
    styleSheet += '''
        QDockWidget {
            border: @widget-border@;
            border-radius: 4px;
            background-color: @dock-color@;
            color: @text-color@;
        }

        QDockWidget::title {
            border: 1px outset rgb(15, 18, 20);
            border-radius: 4px;
            background-color: @dark@;
            position: relative;
            padding-left: 5px;
            text-align: left center;
        }

        QDockWidget::float-button {
            border: none;
            border-radius: 5px;
            width: 3px;
            height: 3px;
            background: qlineargradient(x1: 0, y1: 1, x2: 0, y2: 0,
                stop: 0 rgba(@decorated-color-args@, 5), stop: 1.0 rgba(@decorated-color-args@, 192));
            right: 22px;
            top: 3px;
        }

        QDockWidget::float-button:hover {
            background: qlineargradient(x1: 0, y1: 1, x2: 0, y2: 0,
                stop: 0 rgba(@decorated-color-args@, 32), stop: 1.0 rgba(@decorated-color-args@, 244));
        }

        QDockWidget::float-button:pressed {
            background: qlineargradient(x1: 0, y1: 1, x2: 0, y2: 0,
                stop: 0 rgba(@decorated-color-args@, 128), stop: 1.0 rgba(@decorated-color-args@, 255));
        }

        QDockWidget::close-button {
            border: none;
            border-radius: 5px;
            width: 3px;
            height: 3px;
            background: qlineargradient(x1: 0, y1: 1, x2: 0, y2: 0,
                stop: 0 rgba(@decorated-color-args@, 5), stop: 1.0 rgba(@decorated-color-args@, 192));
            right: 3px;
            top: 3px;
        }

        QDockWidget::close-button:hover {
            background: qlineargradient(x1: 0, y1: 1, x2: 0, y2: 0,
                stop: 0 rgba(@decorated-color-args@, 32), stop: 1.0 rgba(@decorated-color-args@, 244));
        }

        QDockWidget::close-button:pressed {
            background: qlineargradient(x1: 0, y1: 1, x2: 0, y2: 0,
                stop: 0 rgba(@decorated-color-args@, 128), stop: 1.0 rgba(@decorated-color-args@, 255));
        }
    '''

    # QLineEdit style
    styleSheet += '''
        QLineEdit {
            color: @text-color@;
            background-color: @line-edit-background@;
            border: @widget-border@;
            border-style: inset;
            border-radius: 4px;
        }

        QLineEdit:disabled {
            color: @mid-text-color@;
            background-color: @line-edit-background-disabled@;
            border-color: @light-window-color@;
        }

        QLineEdit:focus {
            border-color: rgba(@decorated-color-args@, 192);
        }

        TreeDataEdit[invalid=true] {
            color: red;
        }

        NodeLineEdit[editing=true] {
            border-color: yellow;
        }

        NodeLineEdit[invalid=true] {
            color: red;
        }

        ItemLineEdit:focus {
            border-color: yellow;
        }

        ItemLineEdit[invalid=true] {
            color: red;
        }
    '''

    # # TreeDataEdit style
    # styleSheet += '''
    #     TreeDataEdit {
    #         color: @decorated-color@;
    #         background-color: white;
    #         border: @widget-border@;
    #         border-radius: 3px;
    #     }
    # '''

    # QPushButton style
    styleSheet += '''
        QPushButton {
            color: @text-color@;
            border: 1px outset rgb(100, 103, 105);
            border-radius: 4px;
            padding: 4px 10px 4px 10px;
        }

        QPushButton:disabled {
            color: @dark-text-color@;
            border: 1px outset @background-color@;
            /*background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 @window-color@, stop: 0.45 @light-window-color@,
                stop: 0.55 @light-window-color@, stop: 1.0 @window-color@);*/
            background: @light-window-color@;
        }

        QPushButton:disabled:checked {
            padding: 5px 8px 3px 12px;
            color: @dark-text-color@;
            border: 1px inset @background-color@;
            /*background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 @dark-window-color@, stop: 0.45 @light-window-color@,
                stop: 0.55 @light-window-color@, stop: 1.0 @dark-window-color@);*/
            background: @window-color@;
        }

        QPushButton:enabled {
            color: @text-color@;
            /*background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 @window-color@, stop: 0.4 @background-color@,
                stop: 0.6 @background-color@, stop: 1.0 @window-color@);*/
            background: @background-color@;
        }

        QPushButton:enabled:hover {
            color: @bright-text-color@;
            border: 1px outset @midlight-text-color@;
            /*background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 @light-window-color@, stop: 0.4 @alternate-light-background-color@,
                stop: 0.6 @alternate-light-background-color@, stop: 1.0 @light-window-color@);*/
            background: @alternate-light-background-color@;
        }

        QPushButton:enabled:checked:hover {
            padding: 5px 8px 3px 12px;
            color: @midlight-text-color@;
            border: 1px inset @dark-text-color@;
            /*background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 @window-color@, stop: 0.4 @light-background-color@,
                stop: 0.6 @light-background-color@, stop: 1.0 @window-color@);*/
            background: @light-background-color@;
        }

        QPushButton:enabled:pressed, QPushButton:enabled:checked {
            padding: 5px 8px 3px 12px;
            border: 1px inset @light-background-color@;
            color: @mid-text-color@;
            /*background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 @dark@, stop: 0.4 @window-color@,
                stop: 0.6 @window-color@, stop: 1.0 @dark@);*/
            background: @dark-window-color@;
        }

        SubmitButton:enabled {
            border-style: solid;
            border-top-color: red;
            border-bottom-color: red;
            border-left-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 red, stop: 0.4 @light-background-color@,
                stop: 0.6 @light-background-color@, stop: 1.0 red);
            border-right-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 red, stop: 0.4 @light-background-color@,
                stop: 0.6 @light-background-color@, stop: 1.0 red);
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(255, 0, 0, 192), stop: 0.4 @background-color@,
                stop: 0.6 @background-color@, stop: 1.0 rgba(255, 0, 0, 192));
        }

        SubmitButton:enabled:hover {
            border-style: solid;
            border-top-color: red;
            border-bottom-color: red;
            border-left-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 red, stop: 0.45 @light-background-color@,
                stop: 0.55 @light-background-color@, stop: 1.0 red);
            border-right-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 red, stop: 0.45 @light-background-color@,
                stop: 0.55 @light-background-color@, stop: 1.0 red);
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(255, 0, 0, 224), stop: 0.45 @alternate-light-background-color@,
                stop: 0.55 @alternate-light-background-color@, stop: 1.0 rgba(255, 0, 0, 224));
        }

        SubmitButton:enabled:pressed {
            color: @midlight-text-color@;
            border-style: solid;
            border-top-color: rgba(0, 255, 0, 224);
            border-bottom-color: rgba(0, 255, 0, 224);
            border-left-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(0, 255, 0, 224), stop: 0.45 @light-background-color@,
                stop: 0.55 @light-background-color@, stop: 1.0 rgba(0, 255, 0, 224));
            border-right-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(0, 255, 0, 224), stop: 0.45 @light-background-color@,
                stop: 0.55 @light-background-color@, stop: 1.0 rgba(0, 255, 0, 224));
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(0, 244, 0, 204), stop: 0.4 @dark-window-color@,
                stop: 0.6 @dark-window-color@, stop: 1.0 rgba(0, 244, 0, 204));
        }
    '''

    # QGroupBox style
    styleSheet += '''
        QGroupBox:enabled {
            background: @light-window-color@;
            border: 1px outset @dark-text-color@;
            border-radius: 5px;
            margin-top: 1ex; /* leave space at the top for the title */
        }

        QGroupBox::title:enabled {
            color: @text-color@;
            subcontrol-origin: margin;
            left: 10px;
            top: -3px;
            padding-left: 2px;
        }

        QGroupBox:!enabled {
            background: @dark-window-color@;
            border: 1px inset @light-window-color@;
            border-radius: 5px;
            margin-top: 1ex; /* leave space at the top for the title */
        }

        QGroupBox::title:!enabled {
            color: @dark-text-color@;
            subcontrol-origin: margin;
            left: 10px;
            top: -3px;
            padding-left: 2px;
        }
    '''

    # QRadioButton style
    styleSheet += '''
        QRadioButton:!enabled {
            color: @dark-text-color@;
        }
    '''

    # QComboBox style
    styleSheet += '''
        QComboBox {
            color: @text-color@;
            padding: 1px 18px 1px 3px;
            border: @widget-border@;
            border-color: rgb(15, 18, 20);
            border-radius: 3px;
            min-width: 6em;
        }

        QComboBox:editable {
            background-color: @combobox-background@;
        }

        QComboBox:editable:focus {
            border-color: rgba(@decorated-color-args@, 192);
        }

        QComboBox:!editable {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 @window-color@, stop: 0.45 @background-color@,
                stop: 0.55 @background-color@, stop: 1.0 @window-color@);
        }

        QComboBox:!editable:on {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 @dark@, stop: 0.48 @window-color@,
                stop: 0.52 @window-color@, stop: 1.0 @dark@);
        }

        QComboBox::drop-down {
            border: @widget-border@;
            border-color: rgb(15, 18, 20);
            border-radius: 3px;
            background-color: @window-color@;
        }

        QComboBox::down-arrow {
            border: 1px outset @dark@;
            width: 2px;
            height: 2px;
            background: @decorated-color@;
        }

        QComboBox::down-arrow:hover {
            border: 1px outset @dark@;
            width: 4px;
            height: 4px;
            background: @decorated-color@;
        }

        QComboBox::down-arrow:pressed {
            border: 1px inset @dark@;
            width: 5px;
            height: 5px;
            background: @active-decorated-color@;
        }
    '''

    # QListView
    styleSheet += '''
        QListView {
            selection-color: @dark@;
            selection-background-color: @decorated-color@;
        }
    '''

    # QMenu style
    styleSheet += '''
        QMenu {
            color: @text-color@;
            border: 1px solid @dark-window-color@;
            background-color: @window-color@;
        }

        QMenu::item {
            padding: 2px 25px 2px 25px;
        }

        QMenu::item:disabled {
            color: @dark-text-color@;
        }

        QMenu::item:disabled:selected {
            color: rgba(@decorated-color-args@, 128);
        }

        QMenu::item:selected {
            color: @decorated-color@;
        }
    '''

    # QMenuBar style
    styleSheet += '''
        QMenuBar {
            color: @text-color@;
            background-color: @window-color@;
        }

        QMenuBar::item {
            padding: 1px 4px;
            background-color: @window-color@;
        }

        QMenuBar::item:selected {
            color: @decorated-color@;
        }

        QMenuBar::item:pressed {
            color: @decorated-color@;
        }
    '''

    # QTreeView style
    styleSheet += '''
        QTreeView {
            border: @widget-border@;
            border-radius: 4px;
            background-color: @background-color@;
            alternate-background-color: @alternate-background-color@;
        }

        QTreeView::indicator {
            color: black;
            selection-color: none;
            background-color: black;
            border-color: black;
        }

        QTreeView::item:hover {
            color: rgba(@decorated-color-args@, 144);
            border: none;
        }

        QTreeView::item:selected {
            color: @decorated-color@;
            border: none;
        }

        QTreeView::item:selected:!active {
            color: rgba(@decorated-color-args@, 192);
        }
    '''

    # QHeaderView style
    styleSheet += '''
        QHeaderView::section {
            color: @bright-text-color@;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 @window-color@, stop: 0.5 @light-window-color@, stop: 1.0 @light-background-color@);
        }
    '''

    # QTabWidget style
    styleSheet += '''
        QTabWidget::pane {
            border: 1px solid transparent;
        }

        QTabWidget::tab-bar {
            left: 5px;
        }

        QTabBar::tab {
            color: @bright-text-color@;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 @window-color@, stop: 1.0 @scene-color@);
            border: 1px solid black;
            border-bottom-color: @scene-color@;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            min-width: 8ex;
            padding: 2px 6px 2px 6px;
        }

        QTabBar::tab:selected, QTabBar::tab:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 @light-background-color@, stop: 1.0 @scene-color@);
        }

        QTabBar::tab:selected {
            color: @decorated-color@;
            border-color: black;
            border-bottom-color: @scene-color@;
        }

        QTabBar::tab:selected:hover {
            color: @decorated-color@;
            border-color: @hover-tab-border@;
            border-bottom-color: @scene-color@;
        }

        QTabBar::tab:hover {
            color: @text-color@;
            border-color: @hover-tab-border@;
        }

        QTabBar::tab:!selected {
            color: @mid-text-color@;
            margin-top: 4px;
        }
    '''

    # QGraphicsView style
    styleSheet += '''
        QGraphicsView {
            border: @widget-border@;
            border-style: inset;
            border-width: 2px;
            border-radius: 4px;
            background-color: @scene-color@;
        }
    '''

    # QScrollBar style
    styleSheet += '''
        QScrollBar:vertical {
            background-color: transparent;/*@background-color@;*/
            width: 10px;
            /*margin: 12px 1px 12px 1px;*/
            margin: 2px 1px 2px 1px;
        }

        QScrollBar:horizontal {
            background-color: transparent;/*@background-color@;*/
            height: 10px;
            /*margin: 1px 12px 1px 12px;*/
            margin: 1px 2px 1px 2px;
        }

        QScrollBar[moving=true] {
            background-color: rgba(0, 0, 0, 64);
        }

        QScrollBar:hover {
            background-color: rgba(0, 0, 0, 64);
        }

        QScrollBar::add-page, QScrollBar::sub-page {
            background: none;
        }

        QScrollBar::handle {
            border-width: 1px;
            border-radius: 4px;
            border-style: inset;
            background-color: gray;
        }

        QScrollBar::handle:vertical[parentFocus=true] {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(@decorated-color-args@, 112), stop: 0.4 rgba(@decorated-color-args@, 176),
                stop: 0.5 rgba(@decorated-color-args@, 204), stop: 0.8 rgba(@decorated-color-args@, 224),
                stop: 1.0 rgba(@decorated-color-args@, 132));
        }

        QScrollBar::handle:vertical:hover {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(@decorated-color-args@, 132), stop: 0.4 rgba(@decorated-color-args@, 204),
                stop: 0.5 rgba(@decorated-color-args@, 232), stop: 0.8 rgba(@decorated-color-args@, 248),
                stop: 1.0 rgba(@decorated-color-args@, 154));
        }

        QScrollBar::handle:vertical:pressed, QScrollBar::handle:vertical[moving=true] {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(@decorated-color-args@, 192), stop: 0.4 rgba(@decorated-color-args@, 224),
                stop: 0.5 rgba(@decorated-color-args@, 244), stop: 0.8 rgba(@decorated-color-args@, 255),
                stop: 1.0 rgba(@decorated-color-args@, 208));
        }

        QScrollBar::handle:horizontal[parentFocus=true] {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(@decorated-color-args@, 112), stop: 0.4 rgba(@decorated-color-args@, 176),
                stop: 0.5 rgba(@decorated-color-args@, 204), stop: 0.8 rgba(@decorated-color-args@, 224),
                stop: 1.0 rgba(@decorated-color-args@, 132));
        }

        QScrollBar::handle:horizontal:hover {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(@decorated-color-args@, 132), stop: 0.4 rgba(@decorated-color-args@, 204),
                stop: 0.5 rgba(@decorated-color-args@, 224), stop: 0.8 rgba(@decorated-color-args@, 248),
                stop: 1.0 rgba(@decorated-color-args@, 154));
        }

        QScrollBar::handle:horizontal:pressed, QScrollBar::handle:horizontal[moving=true] {
            background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(@decorated-color-args@, 192), stop: 0.4 rgba(@decorated-color-args@, 224),
                stop: 0.5 rgba(@decorated-color-args@, 244), stop: 0.8 rgba(@decorated-color-args@, 255),
                stop: 1.0 rgba(@decorated-color-args@, 208));
        }

        QScrollBar::add-line, QScrollBar::sub-line {
            border: none;
            background: none;
            /*border: 1px solid black;
            background-color: @window-color@;*/
        }

        /*QScrollBar::add-line:vertical {
            height: 10px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }

        QScrollBar::sub-line:vertical {
            height: 10px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }

        QScrollBar::add-line:horizontal {
            width: 10px;
            subcontrol-position: right;
            subcontrol-origin: margin;
        }

        QScrollBar::sub-line:horizontal {
            width: 10px;
            subcontrol-position: left;
            subcontrol-origin: margin;
        }

        QScrollBar::left-arrow:horizontal,
        QScrollBar::right-arrow:horizontal,
        QScrollBar::up-arrow:vertical,
        QScrollBar::down-arrow:vertical
        {
            border: 1px solid black;
            width: 2px;
            height: 2px;
            background-color: @decorated-color@;
        }

        QScrollBar::left-arrow:horizontal:hover,
        QScrollBar::right-arrow:horizontal:hover,
        QScrollBar::up-arrow:vertical:hover,
        QScrollBar::down-arrow:vertical:hover
        {
            border: 1px solid black;
            width: 4px;
            height: 4px;
            background-color: @decorated-color@;
        }

        QScrollBar::left-arrow:horizontal:pressed,
        QScrollBar::right-arrow:horizontal:pressed,
        QScrollBar::up-arrow:vertical:pressed,
        QScrollBar::down-arrow:vertical:pressed
        {
            border: 1px solid black;
            width: 4px;
            height: 4px;
            background-color: @active-decorated-color@;
        }*/
    '''

    # StateDebugWidget - debugger server widget
    styleSheet += '''
        StateDebugWidget {
            border: @widget-border@;
            border-radius: 4px;
        }
    '''

    styleSheet += '''
        QMessageBox {
            background: @message-box-color@;
        }
    '''

    while '@' in styleSheet:
        for d in definition_table:
            styleSheet = styleSheet.replace(d, definition_table[d])

    application.setStyleSheet(styleSheet)

#######################################################################################################################
#######################################################################################################################

