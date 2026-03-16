# Very basic NTRIP client for microPython platforms - nominally ESP32/Airlift
#
# SJM@MCL Aug 24
#
# https://github.com/mcl-uk/Simple_uPy_NTRIP_Client
#
#   Inspired by:
#   https://github.com/jcmb/NTRIP/blob/master/NTRIP%20Client/NtripClient.py
#   This is free and open code, redistribute it and/or modify it at will.
#   It is distributed in the hope that it will be useful but without any kind of
#   warranty, implied or otherwise.
#
# Description:
#   Receives the RTCM binary data stream from the specified NTRIP caster and routes it to
#   UART#1 at the specified baud-rate. Simply set the operating parameters to suit your
#   application and save to your target device as main.py.
#
#   It's assumed that micropython is installed on the ESP32 and that a Wifi internet
#   connection has already been established by boot.py. Example boot.py code which sets
#   up Wifi is widely available.
#
# Notes:
#   This code has been tested on an Adafruit Airlift ESP32 WROOM-32E module but should
#   work on any other ESP32 (or non-ESP32) microPython platform. Debug data is available
#   on the module's 'TxD' pin (UART#0 tx @115200Bd) and the received RTCM serial data is
#   output via UART#1 tx mapped to IO33, the Airlift's 'BUSY' pin. Use its TxD, RxD,
#   /RST & IO0 pins to flash & program the unit - but once set up you just need GND, 5v
#   and the 'BUSY' pin for your RTCM data stream output.
#
#   I like the Airlift module for embedded projects because, unlike most ESP dev
#   boards, it does not waste space and power with a built-in USB-to-serial adapter.
#   https://www.adafruit.com/product/4201
#
#   The down side is that flashing/programming/debugging does require an external adapter,
#   suitable FTDI/CP2102/CH340 units are widely available and fine if you're happy to
#   manually sequence the RST and IO0 pins. But for smarter, hassle-free flashing with
#   ESPTool an adapter with RTS & DTR outputs (RTS connects to ESP32_RST/EN & DTR to
#   ESP32_IO0) may be worth the investment.  _BUT_ to be able to use the _same_ adapter
#   for susequent software dev work with tools like Thonny or Ampy it should also
#   incorporate Nodemcu-32s's DTR/RTS mod, see the USBToTTL schematics here:
#   https://docs.ai-thinker.com/_media/esp32/docs/nodemcu-32s_product_specification.pdf
#   Note in particular VT1,VT2,C1 & the two 12K resistors. The modification circumvents
#   the situation where both DTR and RTS are asserted low by default during virtual
#   comm port driver initialisation on a host PC thus causing the ESP32 to be held in
#   reset. Meanwhile, critically, the presence of C1 allows ESPTool to put the device
#   into bootloader mode despite the prevention of static simultaneous low states on
#   DTR & RTS. Such modified adapters are hard to find (I built my own) but here's an
#   example:
#   https://kjdelectronics.com/products/capuf-esp32-programmer
#   Note the helpful diagram showing the 6-wire interface to the ESP32.
#
#   Once flashed with the micropython binary you can continue to use the adapter with
#   a tool such as Thonny to copy your boot.py and main.py files over to the ESP32.
#   And when they're in place the unit will just auto-run, on its own, at power-up.
#
#   Normally, by default, UART#1's recommended pins would be 10,9 (tx,rx) but if using
#   an Adafruit Airlift module pls set UART#1's pins to 33,9 so as to use the 'BUSY' pin
#   (pin8 on the 12 way connector) for serial data output, which will be at 3.3v.
#   If using other, more conventially wired dev boards stick to the 10,9 config.
#
#   The baud rate for UART#1 (the RTCM data stream) is set at 115200 which is pretty
#   much the optimal rate for this application bearing in mind the per-second quantity
#   of RTCM data, the UART driver's buffer size and the loop's sleep time. Changing it
#   might have unexpected consequences, take care.
#
#   Observed power consumption averages at around 40mA with no more than 300mA peaks,
#   measured at 5V on a WROOM-32E based Adafruit Airlift module.

# Change log
#   14-08-24 v0.1 Posted to github
#   15-08-24 v0.2 Added watchdog for RTCM data stream
#                 Added optional confidence LED

# ------------------------------ libs -------------------------------

import subprocess
import socket
import time
import base64

from pathlib import Path

# ------------------------ Operating paramteres --------------------

ntripCaster = "rtk2go.com"  # your preferred caster here
userNamePwd = "xxxx@xxxx.xxxx:none"  # your <email>:<pwd> here
# no pwd rqd for rtk2go clients, use 'none'
mountPoint = "FRELIH"  # your preferred mount point here
myLat, myLon = 46.486149638, 13.825585396  # Gozd Martuljek Zg. Rute 99
# myLat, myLon = 46.046284984, 14.516882957  # Ljubljana Zemljemerska 12
myAlt = 752  # your local altitude in metres here
# myAlt = 296  # Ljubljana
noDataTimeLim = 30  # no-data watch-dog timeout in seconds
userAgent = "Dumb uPyNTRIP Client/0.2"

ntripPort = 2101
ntripHost = False  # Host not tested
ntripV2 = False  # V2 not tested
file = "base.rtcm3"
userBreak = False

# --------------------- globals/objects ------------------------------

byteCounter = 0
uNamePwdB64 = base64.b64encode(bytes(userNamePwd, 'ascii')).decode().strip()

ntripSkt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# ------------------------ support functions --------------------------

def makeGGABytes():
    hour, minute, second = time.gmtime()[3:6]
    # sanitise lat/lon
    NS = "N"
    EW = "E"
    lon = myLon
    lat = myLat
    if lon > 180:
        lon -= 360
        lon *= -1
        EW = "W"
    elif (lon < 0) and (lon >= -180):
        lon *= -1
        EW = "W"
    elif lon < -180:
        lon += 360
    if lat < 0:
        lat *= -1
        NS = "S"
    lonDeg = int(lon)
    latDeg = int(lat)
    lonMin = (lon - lonDeg) * 60
    latMin = (lat - latDeg) * 60
    # construct GGA sentence
    timStr = "{:02d}{:02d}{:02d}.00".format(hour, minute, second)
    latStr = "{:02d}{:011.8f},{:s}".format(latDeg, latMin, NS)
    lonStr = "{:02d}{:011.8f},{:s}".format(lonDeg, lonMin, EW)
    altStr = "{:5.3f}".format(myAlt)
    ggaStr = f"GPGGA,{timStr},{latStr},{lonStr},1,05,0.19,+00400,M,{altStr},M,,"
    # calc checksum
    cksm = 0
    for char in ggaStr:
        cksm ^= ord(char)
    cksStr = "{:02X}".format(cksm)
    return bytes(f"${ggaStr}*{cksStr}\r\n", 'ascii')


# Try to connect to the caster, return 0 if connected else err code
def casterConnect(casterAddress):
    headerOK = False
    ntripSkt.settimeout(10)
    try:
        ntripSkt.connect(casterAddress)
    except KeyboardInterrupt:
        return -1
    except:
        return 1  # rte during connect attempt
    getRq = f"GET /{mountPoint} HTTP/1.1\r\n"
    getRq += f"User-Agent: {userAgent}\r\n"
    getRq += f"Authorization: Basic {uNamePwdB64}\r\n"
    if ntripHost or ntripV2:
        getRq += f"Host: {ntripCaster}:{ntripPort}\r\n"
    if ntripV2:
        getRq += "Ntrip-Version: Ntrip/2.0\r\n"
    # print(getRq)
    try:
        ntripSkt.sendall(bytes(f"{getRq}\r\n", 'ascii'))
    except:
        return 2  # rte sending get rq
    try:
        bRxHeaders = ntripSkt.recv(4096).split(b"\r\n")
    except OSError:  # time-out
        return 7  # get rq timed-out
    except KeyboardInterrupt:
        return -1
    except:
        return 3  # rte during hdr rx
    for bLine in bRxHeaders:
        try:
            line = bLine.decode().strip()
        except:
            break
        if line == '':
            break
        # print(line)
        if line.upper().startswith('SOURCETABLE'):
            return 4  # Mountpoint not found
        else:
            headerOK |= line.upper().endswith(" 200 OK")
    if not headerOK:
        return 5  # connection problem
    # Send GGA sentence
    gga = makeGGABytes()
    # print(gga.decode())
    try:
        ntripSkt.sendall(gga)
    except:
        return 6  # rte sending GGA sentence
    return 0


def handle_client(client_socket, data):
    #printing what the client sends
    # request = client_socket.recv(1024)
    # print(f"[+] Recieved: {request}")
    #sending back the packet
    try:
        client_socket.send(data)
    except:
        client_socket.close()
        exit(0)
    # print("Na rtk posljem tole: ", len(res))
    # client_socket.close()


# Call frequently to service data transfer
def txfrDataTask():
    global byteCounter
    ntripSkt.settimeout(0.01)
    try:
        bData = ntripSkt.recv(128)
    except OSError:  # time-out
        return 0
    except KeyboardInterrupt:
        return -1
    except:
        return 10  # txfr skt problem
    if len(bData) == 0:
        return 0
    byteCounter += len(bData)
    print(bData)
    with open(file, 'ab') as fw:
        fw.write(bData)

    return 0  # fa
    # iled to write data

def write_rtcm_data(bData):
    with open(file, 'wb') as fw:
        fw.write(bData)
    subprocess.run(
        ["/home/vajnar/Projects/RTKLIB/app/consapp/convbin/gcc/convbin", file])

def stop_ntrip_client():
    global userBreak
    userBreak = True


def start_ntrip_client():
    global userBreak
    global ntripSkt
    global byteCounter

    if not ntripSkt:
        ntripSkt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    byteCounter = 0
    userBreak = False

    if Path(file).exists():
        Path(file).unlink()

    err = 0
    casterAddress = ('0.0.0.0', ntripPort)  # (IP,port) tuple, placeholder

    try:
        casterAddress = socket.getaddrinfo(ntripCaster, ntripPort)[0][-1]
    except:
        print('DNS lookup for', ntripCaster, 'failed!')
        err = 9  # addr look-up failed

    noDataTimer = 0
    lastBCnt = 0
    lastSec = int(time.time())
    try:
        assert err == 0
        err = casterConnect(casterAddress)
        print('---', err)

        while err == 0 and not userBreak:  # ------------------- main loop --------------------

            time.sleep(0.01)  # at 115KB ~11ms is rqd to txfr 128 bytes (uart has 256B buffer)
            tNow = int(time.time())
            err = txfrDataTask()  # rxcvs up to 128 bytes per call

            # your additional code here

            # Once a second...
            if lastSec != tNow:
                lastSec = tNow
                # indicate progress: output bytes counted since last update
                if lastBCnt != byteCounter:
                    # print('@{:11d} {:10d} Bytes'.format(tNow, byteCounter - lastBCnt))
                    lastBCnt = byteCounter
                    noDataTimer = 0
                else:
                    # RTCM data watch-dog
                    noDataTimer += 1
                    if noDataTimer > noDataTimeLim:
                        err = 20

    except KeyboardInterrupt:
        err = -1

    if err > 0:
        print(f"Error #{err} connecting / transferring RTCM data")
        print("Resetting for re-try in 10s...")
        time.sleep(10)

    if err < 0 and userBreak:
        print("\r\n^C user exit")
    try:
        ntripSkt.close()
        ntripSkt = None
    except:
        pass

    subprocess.run(
        ["/home/vajnar/Projects/RTKLIB/app/consapp/convbin/gcc/convbin", file])
