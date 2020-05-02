#!/usr/bin/env python3
import sys
import os
import signal
import time
import asyncio
import serial

TCP_PORT = 7777
TCP_IP = '0.0.0.0'
DEVICE = "/dev/ttyUSB0"
BAUD = 9600
SERIAL_TIMEOUT = 1

FOOTER = b"\x10\x03"
DATA_READY = b"\x10\x02"

class TCPSerialBridge(asyncio.Protocol):
	ser = None

	def connect_serial(self, device=DEVICE, baud=BAUD):
		if TCPSerialBridge.ser is None:
			print("SERIAL OPEN!")
			TCPSerialBridge.ser = serial.Serial(device, baudrate=baud, timeout=1)

	def hello_serial(self):
		print("SERIAL HELLO!")
		print("WRITE: 02")
		TCPSerialBridge.ser.write(b"\x02")
		s = TCPSerialBridge.ser.read(1)
		print(f"READ: {s.hex()}\n")
		if s != b"\x10":
			 raise IOError("Error: heat pump does not respond - is it connected?")
		 
	def connected(self):
		if ser is not None:
			try:
				self.hello_serial()
				return True
			except:
				pass
		return False

	def close_serial(self):
		if TCPSerialBridge.ser is not None:
			print("SERIAL CLOSE!")
			TCPSerialBridge.ser.close()
			TCPSerialBridge.ser = None

	def connection_made(self, transport):
		self.transport = transport
		self.address = transport.get_extra_info('peername')
		#self.close_serial()
		#self.connect_serial()

	def connection_lost(self, exc):
		#self.close_serial()
		pass

	def data_received(self, data):
		try:
			flag_open = False
			flag_read = False
			if data.startswith(b"CLOSE"):
				self.close_serial()
				return
			if data.startswith(b"CONNECT"):
				flag_open = True
				self.close_serial()
				self.connect_serial()
				data = data[7:]
			if data.startswith(b"HELLO"):
				self.hello_serial()
				data = data[5:]
			if data.startswith(b"READ"):
				flag_read = True
				data = data[4:]

			print("CLIENT -> SERVER")
			print(f"{self.address} -> {TCP_IP}")
			print(f"RAW: {data.hex()}")
			print()
			TCPSerialBridge.ser.write(data)
			response = bytes()
			if flag_read:
				response = TCPSerialBridge.ser.read(2)
			else:
				response = TCPSerialBridge.ser.read(100)

			print("CLIENT <- SERVER")
			print(f"{self.address} <- {TCP_IP}")
			print(f"RAW: {response.hex()}")
			self.transport.write(response)

			if flag_read and response == DATA_READY:
				print("\nWRITE: 10\n")
				self.ser.write(b"\x10")
				response = TCPSerialBridge.ser.read_until(FOOTER)
				print("CLIENT <- SERVER")
				print(f"{self.address} <- {TCP_IP}")
				print(f"RAW: {response.hex()}")
				self.transport.write(response)
			print()
			print("----------------------------------------------")
			print()
		except Exception as x:
			print(x)

async def serve(host, port):
	loop = asyncio.get_running_loop()
	server = await loop.create_server(TCPSerialBridge, host, port)
	await server.serve_forever()

def handler(signum, frame):
	exit()

def exit():
	quit()

def main():
	signal.signal(signal.SIGINT, handler)
	asyncio.run(serve(TCP_IP, TCP_PORT))


if __name__== "__main__":
	main()

