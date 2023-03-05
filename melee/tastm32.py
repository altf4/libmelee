#!/usr/bin/env python3
import sys
import os
import serial
import struct
import time
import gc

DEBUG = False

int_buffer = 1024 # internal buffer size on replay device

latches_per_bulk_command = 28
packets = 4

VALID_PLAYERS = {
    "n64": (1,5,),
    "snes": (1,2,3,4,5,6,7,8,),
    "nes": (1,5,),
    "gc": (1,),
    "genesis": (1,5,)
}

int_to_byte_struct = struct.Struct('B')
def int_to_byte(interger):
    return int_to_byte_struct.pack(interger)

class TAStm32():
    def __init__(self, ser):
        self.ser = ser
        self.activeRuns = {b'A': False, b'B': False, b'C': False, b'D': False}

    def get_run_prefix(self):
        if self.activeRuns[b'A']:
            if self.activeRuns[b'B']:
                if self.activeRuns[b'C']:
                    if self.activeRuns[b'D']:
                        return None
                    else:
                        self.activeRuns[b'D'] = True
                        return b'D'
                else:
                    self.activeRuns[b'C'] = True
                    return b'C'
            else:
                self.activeRuns[b'B'] = True
                return b'B'
        else:
            self.activeRuns[b'A'] = True
            return b'A'

    def write(self, data):
        count = self.ser.write(data)
        if DEBUG and data != b'':
            print('S:', data)
        return count

    def read(self, count):
        data = self.ser.read(count)
        if DEBUG and data != b'':
            print('R:', data)
        return data

    def reset(self):
        c = self.read(1)
        if c == '':
            pass
        else:
            numBytes = self.ser.inWaiting()
            if numBytes > 0:
                c += self.read(numBytes)
        self.write(b'R')
        time.sleep(0.1)
        data = self.read(2)
        if data == b'\x01R':
            return True
        else:
            return False

    def enable_controller(self):
        self.write(b'C1')

    def disable_controller(self):
        self.write(b'C0')

    def enable_relay(self):
        self.write(b'r1')

    def disable_relay(self):
        self.write(b'r0')

    def power_on(self):
        self.write(b'P1')

    def power_off(self):
        self.write(b'P0')

    def power_soft_reset(self):
        self.write(b'PS')

    def power_hard_reset(self):
        self.write(b'PH')

    def ping(self):
        self.write(b'\xAA')

    def waitForPong(self):
        readCount = 0
        start = time.time()
        while True:
            try:
                if time.time() > start+15:
                    return -1
                c = self.read(1)
                if c == '':
                    continue
                readCount += 1
                if c == b'\x55':
                    return 0
                if readCount > 1000:
                    return -2
            except serial.SerialException:
                return -3
            except KeyboardInterrupt:
                return -4

    def set_bulk_data_mode(self, prefix, mode):
        command = b''.join([b'Q', prefix, mode])
        self.write(command)

    def send_transition(self, prefix, frame, mode):
        if self.activeRuns[prefix]:
            command = ''
            if mode == b'N':
                # Set Normal Mode
                command = b''.join([b'T', prefix, mode, struct.pack('I', frame)])
            elif mode == b'A':
                # Set ACE Mode
                command = b''.join([b'T', prefix, mode, struct.pack('I', frame)])
            elif mode == b'S':
                # Set Soft Reset
                command = b''.join([b'T', prefix, mode, struct.pack('I', frame)])
            elif mode == b'H':
                # Set Hard Reset
                command = b''.join([b'T', prefix, mode, struct.pack('I', frame)])
            elif mode == b'R':
                # Wait for next rumble
                command = b''.join([b'T', prefix, mode, struct.pack('I', frame)])
            if command != '':
                self.write(command)

    def send_latchtrain(self, prefix, latchtrain):
        if self.activeRuns[prefix]:
            command = b''.join([b'U', prefix, struct.pack('H', len(latchtrain)), *[struct.pack('H', i) for i in latchtrain]])
            self.write(command)

    def setup_run(self, console, players=[1], dpcm=False, overread=False, clock_filter=0):
        prefix = self.get_run_prefix()
        if prefix == None:
            raise RuntimeError('No Free Run')
        vp = VALID_PLAYERS.get(console, ())
        if console == 'n64':
            cbyte = b'M'
            pbyte = 0
            for player in players:
                p = int(player)
                if p in vp:
                    pbyte = pbyte ^ 2**(8-p)
                else:
                    raise RuntimeError('Invalid player for N64')
            sbyte = 0
        elif console == 'snes':
            cbyte = b'S'
            pbyte = 0
            for player in players:
                p = int(player)
                if p in vp:
                    pbyte = pbyte ^ 2**(8-p)
                else:
                    raise RuntimeError('Invalid player for SNES')
            sbyte = 0
            if dpcm:
                sbyte = sbyte ^ 0x80
            if overread:
                sbyte = sbyte ^ 0x40
            if clock_filter:
                sbyte = sbyte + clock_filter
        elif console == 'nes':
            cbyte = b'N'
            pbyte = 0
            for player in players:
                p = int(player)
                if p in vp:
                    pbyte = pbyte ^ 2**(8-p)
                else:
                    raise RuntimeError('Invalid player for NES')
            sbyte = 0
            if dpcm:
                sbyte = sbyte ^ 0x80
            if overread:
                sbyte = sbyte ^ 0x40
            if clock_filter:
                sbyte = sbyte + clock_filter
        elif console == 'gc':
            cbyte = b'G'
            pbyte = 0
            for player in players:
                p = int(player)
                if p in vp:
                    pbyte = pbyte ^ 2**(8-p)
                else:
                    raise RuntimeError('Invalid player for GC')
            sbyte = 0
        elif console == 'genesis':
            cbyte = b'J'
            pbyte = 0
            sbyte = 0
            for player in players:
                p = int(player)
                if p in vp:
                    pbyte = pbyte ^ 2**(8-p)
                else:
                    raise RuntimeError('Invalid player for Genesis')
        command = b'S' + prefix + cbyte + int_to_byte(pbyte) + int_to_byte(sbyte)
        self.write(command)
        time.sleep(0.1)
        data = self.read(2)
        if data == b'\x01S':
            return prefix
        else:
            self.activeRuns[prefix] = False
            raise RuntimeError('Error during setup')

    def main_loop(self, run):
        global DEBUG
        frame = 0
        frame_max = len(run.buffer)
        while True:
            try:
                c = self.read(1)
                if c == '':
                    continue
                numBytes = self.ser.inWaiting()
                if numBytes > 0:
                    c += self.read(numBytes)
                    if numBytes > int_buffer:
                        print ("WARNING: High latch rate detected: " + str(numBytes))
                latches = c.count(run.run_id)
                bulk = c.count(run.run_id.lower())
                missed = c.count(b'\xB0')
                if missed != 0:
                    run.fn -= missed
                    print('Buffer Overflow x{}'.format(missed))

                # Latch Trains
                trainskips = c.count(b'UA')
                if trainskips != 0:
                    print(f'--- Extra frame detected. Skipping a frame to compensate. x{trainskips}')
                trainextra = c.count(b'UB')
                if trainextra != 0:
                    print(f'--- Short a frame. Adding a frame to compensate. x{trainextra}')
                trainfin = c.count(b'UC')
                if trainfin != 0:
                    print(f'+++ Latch train success! x{trainfin}')
                trainfailed = c.count(b'UF')
                if trainfailed != 0:
                    print(f'!!! Off by many frames. Run is probably broken. Good luck! x{trainfailed}')
                    sys.exit(1)

                for latch in range(latches):
                    try:
                        data = run.run_id + run.buffer[run.fn]
                        self.write(data)
                        if run.fn % 100 == 0:
                            print('Sending Latch: {}'.format(run.fn))
                    except IndexError:
                        command = []
                        command.append(run.run_id + run.blankframe)
                        data = b''.join(command)
                        self.write(data)
                        pass
                    run.fn += 1
                    frame += 1
                for cmd in range(bulk):
                    for packet in range(packets):
                        command = []
                        for latch in range(latches_per_bulk_command//packets):
                            try:
                                command.append(run.run_id + run.buffer[run.fn])
                                run.fn += 1
                                if run.fn % 100 == 0:
                                    print('Sending Latch: {}'.format(run.fn))
                            except IndexError:
                                command.append(run.run_id + run.blankframe)
                                run.fn += 1
                            frame += 1
                        data = b''.join(command)
                        self.write(data)
                    self.write(run.run_id.lower())
                if frame > frame_max:
                    break
            except serial.SerialException:
                print('ERROR: Serial Exception caught!')
                break
            except KeyboardInterrupt:
                print('^C Exiting')
                break

class RunObject:
    def __init__(self, run_id, buffer, fn, blankframe):
        self.run_id = run_id
        self.buffer = buffer
        self.fn = fn
        self.blankframe = blankframe
