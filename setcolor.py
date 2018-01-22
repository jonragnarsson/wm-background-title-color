from colors import colorz
from urllib.parse import urlparse, unquote
from shutil import copyfile
import xml.etree.ElementTree as ET
from time import sleep
from pathlib import Path
from os import path
import subprocess
import colorsys

xmlpath = 'metacity-1/metacity-theme-3.xml'

Cfocused = ['C_wm_bg_focused', 'C_wm_border' 'C_icon_close_bg']
Cunfocused = ['C_wm_bg_unfocused']
Clighter = ['C_wm_highlight']
Ctitlefocused = ['C_title_focused']
Ctitleunfocused = 'C_title_unfocused'
SATADJUST = -0.2


class Hexnum:

    hexstr = '000000'
    r = 0
    g = 0
    b = 0

    def __init__(self, hexstr='000000'):
        if hexstr[:1] == '#':
            hexstr = hexstr[1:]
        self.hexstr = hexstr
        c = [self.hexstr[i:i + 2] for i in range(0, len(self.hexstr), 2)]
        self.r, self.g, self.b = list(map(lambda x: int(x, 16), c))

    def setrgb(self, r=0, g=0, b=0):
        self.r = r
        self.g = g
        self.b = b
        self.hexstr = '{:02x}{:02x}{:02x}'.format(r, g, b)

    def getrgbf(self):
        return self.r / 255.999, self.g / 255.999, self.b / 255.999

    def setrgbf(self, r=0, g=0, b=0):
        self.r = int(r * 255.999)
        self.g = int(g * 255.999)
        self.b = int(b * 255.999)
        self.hexstr = '{:02x}{:02x}{:02x}'.format(self.r, self.g, self.b)

    def value(self):
        r, g, b = self.getrgbf()
        return colorsys.rgb_to_hsv(r, g, b)[2]

    def hsv(self):
        r, g, b = self.getrgbf()
        return colorsys.rgb_to_hsv(r, g, b)

    def setHSV(self, h, s, v):
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self.setrgbf(r, g, b)

    @staticmethod
    def checklimit(val, min, max):
        if val < min:
            return min
        if val > max:
            return max
        return val

    def adjustHSV(self, h, s, v):
        r, g, b = self.getrgbf()
        hsv = colorsys.rgb_to_hsv(r, g, b)
        H = self.checklimit(hsv[0] + h, 0, 1)
        S = self.checklimit(hsv[1] + s, 0, 1)
        V = self.checklimit(hsv[2] + v, 0, 1)
        r, g, b = colorsys.hsv_to_rgb(H, S, V)
        self.setrgbf(r, g, b)

    def __str__(self):
        return '#{}'.format(self.hexstr)


def gget(path, what):
    with subprocess.Popen(['gsettings', 'get', path, what], stdout=subprocess.PIPE) as proc:
        l = proc.stdout.readline().decode('ascii').strip()
        return l.replace("'", '')


def gset(path, what, value):
    with subprocess.Popen(['gsettings', 'set', path, what, value], stdout=subprocess.PIPE) as proc:
        l = proc.stdout.readline().decode('ascii').strip()
        return l.replace("'", '')


def gwatch(path, what, callback=None):
    # needs threads and callbacks for multiple watches
    with subprocess.Popen(['gsettings', 'monitor', path, what], stdout=subprocess.PIPE) as proc:
        while True:
            l = proc.stdout.readline().decode('ascii').strip()
            if callback:
                callback(l[len(what) + 2:].replace("'", ''))
            else:
                print(l[len(what) + 2:])


def resettheme(theme):
    # gsettings reset org.cinnamon.desktop.wm.preferences theme;
    # gsettings set org.cinnamon.desktop.wm.preferences theme 'Mint-Y-Yltra-Dark'
    with subprocess.Popen(['gsettings', 'reset', 'org.cinnamon.desktop.wm.preferences', 'theme'], stdout=subprocess.PIPE) as proc:
        l = proc.stdout.readline().decode('ascii').strip()
    sleep(0.2)  # sometimes it fails.
    gset('org.cinnamon.desktop.wm.preferences', 'theme', theme)


def brightest(hexcols):
    v = 0.0  # black as my ex heart
    currh = ''
    for _ in hexcols:
        h = Hexnum(_)
        if h.value() > v:
            v = h.value()
            currh = _
    return currh


def darkest(hexcols):
    v = 1.0  # hsv white
    currh = ''
    for _ in hexcols:
        h = Hexnum(_)
        if h.value() < v:
            v = h.value()
            currh = _
    return currh


def updatexml(rawuri):
    url = urlparse(rawuri)
    colors = list(colorz(unquote(url.path), 3))
    print(unquote(url.path))
    print(colors)
    _base = darkest(colors)
    h = Hexnum(_base)
    # print('base:', h.hsv())
    h.adjustHSV(0, 0, 0.12)
    # print('lighter:', h.hsv())
    _lighter = '#{}'.format(h.hexstr)
    h = Hexnum(_base)
    h.adjustHSV(0, -0.3, 0.05)
    # print('nofocus:', h.hsv())
    _nofocus = '#{}'.format(h.hexstr)
    print('base:', _base, 'nofcus:', _nofocus, 'lighter:', _lighter)
    xf = ET.parse(backup)
    root = xf.getroot()
    for c in root.findall('constant'):
        if c.attrib['name'] in Cfocused:
            c.attrib['value'] = _base
        if c.attrib['name'] in Clighter:
            c.attrib['value'] = _lighter
        if c.attrib['name'] in Cunfocused:
            c.attrib['value'] = _nofocus
        if c.attrib['name'] == 'C_title_unfocused':
            h.adjustHSV(0, -0.3, 0.3)
            c.attrib['value'] = '#'+h.hexstr
    xf.write(fullname)
    resettheme(theme)


userthemes = path.join(str(Path.home()), '.themes/')  # for now
theme = gget('org.cinnamon.desktop.wm.preferences', 'theme')
fullname = path.join(userthemes, theme, xmlpath)
backup = fullname+'_'

if path.isfile(fullname):
    if not path.isfile(backup):
        copyfile(fullname, backup)  # just in case, never work with the original file
        print("Made backup of '{}' file.".format(xmlpath))
else:
    exit("The file '{}' does not exist. You need to copy the theme into your home folder".format(fullname))

print('Theme:', theme)

updatexml(gget('org.cinnamon.desktop.background', 'picture-uri'))  # initial update
gwatch('org.cinnamon.desktop.background', 'picture-uri', updatexml)  # wait for gsettings forever

