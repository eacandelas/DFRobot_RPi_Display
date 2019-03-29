# -*- coding:utf-8 -*-

import time

import sys
sys.path.append("..")

from dfrobot_display.dfrobot_display import DFRobot_Display
from display_extension import fonts_8_16 as fonts_ABC

try:
  from dfrobot_interface.raspberry.spi import SPI
  from dfrobot_interface.raspberry.gpio import GPIO
except:
  print("unknow platform")
  exit()

CONFIG_IL0376F = {

}

CONFIG_IL3895 = {
  
}

class DFRobot_Epaper(DFRobot_Display):

  XDOT = 128
  YDOT = 250

  FULL = True
  PART = False

  def __init__(self, width = 250, height = 122):
    DFRobot_Display.__init__(self, width, height)
    # length = width * height // 8
    length = 4000
    self._displayBuffer = bytearray(length)
    i = 0
    while i < length:
      self._displayBuffer[i] = 0xff
      i = i + 1

    self._isBusy = False
    self._busyExitEdge = GPIO.RISING
    
    self._fonts.setFontsABC(fonts_ABC)
    self.setExFontsFmt(16, 16)

  def _busyCB(self, channel):
    self._isBusy = False

  def setBusyExitEdge(self, edge):
    if edge != GPIO.HIGH and edge != GPIO.LOW:
      return
    self._busyEdge = edge

  def begin(self):
    pass
    # self.setBusyCB(self._busyCB)
    # self._powerOn()

  def pixel(self, x, y, color):
    if x < 0 or x >= self._width:
      return
    if y < 0 or y >= self._height:
      return
    x = int(x)
    y = int(y)
    m = int(x * 16 + (y + 1) / 8)
    sy = int((y + 1) % 8)
    if color == self.WHITE:
      if sy != 0:
        self._displayBuffer[m] = self._displayBuffer[m] | int(pow(2, 8 - sy))
      else:
        self._displayBuffer[m - 1] = self._displayBuffer[m - 1] | 1
    elif color == self.BLACK:
      if sy != 0:
        self._displayBuffer[m] = self._displayBuffer[m] & (0xff - int(pow(2, 8 - sy)))
      else:
        self._displayBuffer[m - 1] = self._displayBuffer[m - 1] & 0xfe

  def _setWindow(self, x, y):
    hres = y // 8
    hres = hres << 3
    vres_h = x >> 8
    vres_l = x & 0xff
    self.writeCmdAndData(0x61, [hres, vres_h, vres_l])

  def _initLut(self, mode):
    if mode == self.FULL:
      self.writeCmdAndData(0x32, [0x22,0x55,0xAA,0x55,0xAA,0x55,0xAA,
                                  0x11,0x00,0x00,0x00,0x00,0x00,0x00,
                                  0x00,0x00,0x1E,0x1E,0x1E,0x1E,0x1E,
                                  0x1E,0x1E,0x1E,0x01,0x00,0x00,0x00,0x00])
    elif mode == self.PART:
      self.writeCmdAndData(0x32, [0x18,0x00,0x00,0x00,0x00,0x00,0x00,
                                  0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                                  0x00,0x00,0x0F,0x01,0x00,0x00,0x00,
                                  0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00])

  def _setRamData(self, xStart, xEnd, yStart, yStart1, yEnd, yEnd1):
    self.writeCmdAndData(0x44, [xStart, xEnd])
    self.writeCmdAndData(0x45, [yStart, yStart1, yEnd, yEnd1])

  def _setRamPointer(self, x, y, y1):
    self.writeCmdAndData(0x4e, [x])
    self.writeCmdAndData(0x4f, [y, y1])

  def _init(self):
    self.writeCmdAndData(0x01, [(self.YDOT - 1) % 256, (self.YDOT - 1) // 256, 0x00])
    self.writeCmdAndData(0x0c, [0xd7, 0xd6, 0x9d])
    self.writeCmdAndData(0x2c, [0xa8])
    self.writeCmdAndData(0x3a, [0x1a])
    self.writeCmdAndData(0x3b, [0x08])
    self.writeCmdAndData(0x11, [0x01])
    self._setRamData(0x00, (self.XDOT - 1) // 8, (self.YDOT - 1) % 256, (self.YDOT - 1) // 256, 0x00, 0x00)
    self._setRamPointer(0x00, (self.YDOT - 1) % 256, (self.YDOT - 1) // 256)
  
  def _writeDisRam(self, sizeX, sizeY):
    if sizeX % 8 != 0:
      sizeX = sizeX + (8 - sizeX % 8)
    sizeX = sizeX // 8
    self.writeCmdAndData(0x24, self._displayBuffer[0: sizeX * sizeY])

  def _updateDis(self, mode):
    if mode == self.FULL:
      self.writeCmdAndData(0x22, [0xc7])
    elif mode == self.PART:
      self.writeCmdAndData(0x22, [0x04])
    else:
      return
    self.writeCmdAndData(0x20, [])
    self.writeCmdAndData(0xff, [])

  def _waitBusyExit(self):
    temp = 0
    while self.readBusy() != False:
      time.sleep(0.01)
      temp = temp + 1
      if (temp % 200) == 0:
        print("waitBusyExit")

  def _powerOn(self):
    self.writeCmdAndData(0x22, [0xc0])
    self.writeCmdAndData(0x20, [])

  def _powerOff(self):
    self.writeCmdAndData(0x12, [])
    self.writeCmdAndData(0x82, [0x00])
    self.writeCmdAndData(0x01, [0x02, 0x00, 0x00, 0x00, 0x00])
    self.writeCmdAndData(0x02, [])

  def _disPart(self, xStart, xEnd, yStart, yEnd):
    self._setRamData(xStart // 8, xEnd // 8, yEnd % 256, yEnd // 256, yStart % 256, yStart // 256)
    self._setRamPointer(xStart // 8, yEnd % 256, yEnd // 256)
    self._writeDisRam(xEnd - xStart, yEnd - yStart + 1)
    self._updateDis(self.PART)

  def flush(self, mode):
    if mode != self.FULL and mode != self.PART:
      return
    self._init()
    self._initLut(mode)
    self._powerOn()
    if mode == self.PART:
      self._disPart(0, self.XDOT - 1, 0, self.YDOT - 1)
    else:
      self._setRamPointer(0x00, (self.YDOT - 1) % 256, (self.YDOT - 1) // 256)
      self._writeDisRam(self.XDOT, self.YDOT)
      self._updateDis(mode)
  
  def startDrawBitmapFile(self, x, y):
    self._bitmapFileStartX = x
    self._bitmapFileStartY = y

  def bitmapFileHelper(self, buf):
    for i in range(len(buf) // 3):
      addr = i * 3
      if buf[addr] == 0x00 and buf[addr + 1] == 0x00 and buf[addr + 2] == 0x00:
        self.pixel(self._bitmapFileStartX, self._bitmapFileStartY, self.BLACK)
      else:
        self.pixel(self._bitmapFileStartX, self._bitmapFileStartY, self.WHITE)
      self._bitmapFileStartX += 1
  
  def endDrawBitmapFile(self):
    self.flush(self.PART)

class DFRobot_Epaper_SPI(DFRobot_Epaper):

  def __init__(self, bus, dev, cs, cd, busy):
    DFRobot_Epaper.__init__(self)
    self._spi = SPI(bus, dev)
    self._cs = GPIO(cs, GPIO.OUT)
    self._cd = GPIO(cd, GPIO.OUT)
    self._busy = GPIO(busy, GPIO.IN)
  
  def writeCmdAndData(self, cmd, data = []):
    self._waitBusyExit()
    self._cs.setOut(GPIO.LOW)
    self._cd.setOut(GPIO.LOW)
    self._spi.transfer([cmd])
    self._cd.setOut(GPIO.HIGH)
    self._spi.transfer(data)
    self._cs.setOut(GPIO.HIGH)

  def readBusy(self):
    return self._busy.read()

  def setBusyCB(self, cb):
    self._busy.setInterrupt(self._busyExitEdge, cb)
