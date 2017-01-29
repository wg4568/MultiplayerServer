import socket, base, socket, threading, os, binascii, time, random, eztext

# types of packets:
#	-connect
#	-disconnect clientid
#	-update clientid direction
#	-info clientid var newval
#	-get clientid

HOST = ""
PORT = 5400

def random_string(length=16):
	length /= 2
	return binascii.b2a_hex(os.urandom(length))

def random_color():
	r = random.randint(0, 255)
	g = random.randint(0, 255)
	b = random.randint(0, 255)
	return (r, g, b)

class Client:
	def __init__(self, addr):
		self.addr = addr
		self.cid = random_string()
		self.pid = random_string(length=4)
		self.username = "unnamed-user"
		self.x = 5
		self.y = 5
		self.direction = 1 # 0: up  1: right  2: down  3: left
		self.last_seen = time.time()
		self.server = None
		self.color = random_color()

	def frame(self):
		if self.direction == 0:
			self.y += 1
		if self.direction == 1:
			self.x += 1
		if self.direction == 2:
			self.y -= 1
		if self.direction == 3:
			self.x -= 1

		if time.time() - self.last_seen > self.server.kick_time:
			self.server.client_kick(self.cid, reason="timeout")

	def __str__(self):
		r = self.color[0]
		g = self.color[1]
		b = self.color[2]
		return "%s:%s:%s:%s:%s:%s" % (self.x, self.y, r, g, b, self.pid)

class Server(threading.Thread):
	def __init__(self, host, port):
		threading.Thread.__init__(self)
		self.running = False
		self.host = host
		self.port = port
		self.log = []
		self.game = None
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind((self.host, self.port))
		self.sock.settimeout(0.1)
		self.kick_time = 20
		self.clients = []
		self.commands = []

	def client_kick(self, cid, reason=None):
		addr = self.client_select(cid).addr
		self.sendto("kicked %s" % (reason), addr)
		self.clients = [s for s in self.clients if s.cid != cid]

	def client_select(self, cid):
		for c in self.clients:
			if c.cid == cid or c.username == cid or c.pid == cid:
				return c

	def client_seen(self, cid):
		cl = self.client_select(cid)
		cl.last_seen = time.time()

	def command(self, cmd):
		self.commands.append(cmd)
		cmd = cmd.split()
		if cmd[0] == "stop":
			self.game.stop()
		if cmd[0] == "kick":
			try: reason = cmd[2]
			except IndexError: reason = None
			cl = self.client_select(cmd[1])
			self.client_kick(cl.cid, reason=reason)
		if cmd[0] == "pause":
			self.game.serverticker.server_paused = True
		if cmd[0] == "resume":
			self.game.serverticker.server_paused = False
		if cmd[0] == "set":
			cl = self.client_select(cmd[1])
			if cmd[2] == "username":
				cl.username = cmd[3]
			if cmd[2] == "color":
				if cmd[3] == "random":
					cl.color = random_color()
				else:
					r = int(cmd[3])
					g = int(cmd[4])
					b = int(cmd[5])
					cl.color = (r, g, b)
		if cmd[0] == "rate":
			self.game.serverticker.rate = int(cmd[1])

	def sendto(self, dat, addr):
		self.log.append([dat, addr, "send"])
		self.sock.sendto(dat, addr)

	def parse(self, data, addr):
		data = data.split()
		try:
			if data[0] == "connect":
				nc = Client(addr)
				nc.server = self
				self.clients.append(nc)
				self.sendto("connect %s" % (nc.cid), addr)
			elif data[0] == "disconnect":
				cid = data[1]
				self.client_seen(cid)
				self.client_kick(cid, "disconnect")
				self.sendto("disconnect", addr)
			elif data[0] == "info":
				cid = data[1]
				self.client_seen(cid)
				cl = self.client_select(cid)
				if data[2] == "username":
					cl.username = data[3]
					self.sendto("info username %s" % (cl.username), addr)
				elif data[2] == "color":
					r = int(data[3])
					g = int(data[4])
					b = int(data[5])
					cl.color = (r, g, b)
					self.sendto("info color %s %s %s" % (r, g, b), addr)
				else:
					self.sendto("error", addr)
			elif data[0] == "checkin":
				cid = data[1]
				self.client_seen(cid)
				self.sendto("checkin", addr)
			elif data[0] == "update":
				cid = data[1]
				self.client_seen(cid)
				cl = self.client_select(cid)
				cl.direction = int(data[2])
				self.sendto("update %s" % cl.direction, addr)
			elif data[0] == "get":
				self.sendto("get %s" % (self.client_state), addr)
			else:
				self.sendto("error", addr)
		except Exception as e:
			print e
			self.sendto("error", addr)

	def update_state(self):
		state = ""
		for client in self.clients:
			state += str(client)
			state += "|"
		self.client_state = state[:-1]

	def frame(self):
		self.update_state()
		for c in self.clients:
			c.frame()

	def run(self):
		self.running = True
		while self.running:
			try:
				data, addr = self.sock.recvfrom(1024)
				data = data.replace("\n","")
				self.log.append([data, addr, "recv"])
				self.parse(data, addr)
			except socket.error:
				pass

class ServerTicker(threading.Thread):
	def __init__(self, clock, server):
		threading.Thread.__init__(self)
		self.server = server
		self.running = False
		self.rate = 10
		self.clock = clock
		self.frame = 0

		self.server_paused = False

		self.fps_counter = 0
		self.fps_last_time = time.time()
		self.fps = 0

	def run(self):
		self.running = True
		while self.running:
			if not self.server_paused:
				self.frame += 1
				self.fps_counter += 1
				d = time.time()-self.fps_last_time
				if d >= 1:
					self.fps = round(self.fps_counter * (1.0/d), 1)
					self.fps_counter = 0
					self.fps_last_time = time.time()
				self.server.frame()
				self.clock.tick(self.rate)

class Game(base.Game):
	def __init__(self):
		base.Game.__init__(self)
		self.server = Server(HOST, PORT)
		self.server.game = self
		self.server.start()
		self.serverticker = ServerTicker(self.pygame.time.Clock(), self.server)
		self.serverticker.start()
		self.rate = 60
		self.size = (500, 530)
		self.show_fps = False
		self.background = (255, 255, 255)
		self.title = "UDP Game Server (%s:%s)" % (self.server.host, self.server.port)
		self.font = self.pygame.font.Font('/usr/share/fonts/truetype/msttcorefonts/arial.ttf', 12)
		self.font_large = self.pygame.font.Font('/usr/share/fonts/truetype/msttcorefonts/arial.ttf', 15)
		self.inputbox = eztext.Input(maxlength=45, color=(0, 0, 0), font=self.font_large, x=12, y=501)
		self.cmdpos = -1

	def draw(self):
		self.text("Server log", (10, 10), (0, 0, 0))
		self.text("Connected users", (10, 350), (0, 0, 0))
		self.text("Game overview", (self.r("x", 130), 350), (0, 0, 0))
		self.text("%s ticks/sec" % self.serverticker.fps, (self.r("x", 80), 10), (0, 0, 0))
		self.draw_rect(self.screen, (200, 200, 200), [10, 30, self.r("x", 20), 310])
		self.draw_rect(self.screen, (200, 200, 200), [10, 370, self.r("x", 150), self.r("y", 40)-370])
		self.draw_rect(self.screen, (200, 200, 200), [self.r("x", 130), 370, 120, 120])
		self.draw_rect(self.screen, (200, 200, 200), [10, 500, 480, 20])

		self.inputbox.draw(self.screen)

		for client in self.server.clients:
			if client.x in xrange(50) and client.y in xrange(1,51):
				x = (client.x * 2.4) + self.r("x", 130)
				y = 120 - (client.y * 2.4) + 370
				self.draw_rect(self.screen, client.color, [x, y, 3, 3])

		reqs = self.server.log[::-1]
		if len(reqs) > 10:
			reqs = reqs[:20]
		string = ""
		ypos = 35

		for req in reqs:
			if req[2] == "recv":
				col = (180, 0, 0)
			else:
				col = (80, 80, 80)
			self.text(str(req), (15, ypos), col)
			ypos += 15

		ypos = 375
		for client in self.server.clients:
			self.text("%s (%s, %s, %s:%s, %s)" % (client.username, \
												client.cid, \
												client.pid, \
												client.x, \
												client.y, \
												int(time.time()-client.last_seen)), \
												(15, ypos), \
												client.color \
											 )
			ypos += 15

	def logic(self):
		for e in self.events:
			if e.type == self.pygame.KEYDOWN:
				if e.key == self.pygame.K_UP:
					self.cmdpos += 1
					if self.cmdpos > len(self.server.commands) - 1:
						self.cmdpos = len(self.server.commands) - 1
				if e.key == self.pygame.K_DOWN:
					self.cmdpos -= 1
					if self.cmdpos == -1:
						self.inputbox.value = ""
					if self.cmdpos < -1:
						self.cmdpos = -1
				if e.key == self.pygame.K_ESCAPE:
					self.cmdpos = -1
					self.inputbox.value = ""

		if self.cmdpos > -1:
			self.inputbox.value = self.server.commands[::-1][self.cmdpos]

		ret = self.inputbox.update(self.events)
		if ret:
			self.server.command(ret)
			self.cmdpos = -1

	def on_stop(self):
		self.server.running = False
		self.serverticker.running = False

game = Game()
game.run()