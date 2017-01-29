import socket, base

HOST = "localhost"
PORT = 5400

class Client:
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.cid = None
		self.clients = []

	def ping(self, data, amt=1024):
		self.sock.sendto(data, (self.host, self.port))
		return self.sock.recvfrom(amt)[0]

	def connect(self):
		resp = self.ping("connect")
		self.cid = resp.split(" ")[1]
		return resp

	def info(self, inf, dat):
		resp = self.ping("info %s %s %s" % (self.cid, inf, dat))
		return resp

	def update(self, dr):
		resp = self.ping("update %s %s" % (self.cid, dr))
		return resp

	def get(self):
		respo = self.ping("get")
		try:
			resp = respo.split(" ")[1].split("|")
			clients = []
			for plyr in resp:
				inf = plyr.split(":")
				inf = [int(inf[0]), int(inf[1]), (int(inf[2]), int(inf[3]), int(inf[4]))]
				clients.append(inf)
			self.clients = clients
		except Exception as e:
			print "Bad get response (%s)" % e
		return respo

	def disconnect(self):
		resp = self.ping("disconnect %s" % (self.cid))
		return resp

	def checkin(self):
		resp = self.ping("checkin %s" % (self.cid))
		return resp

class Game(base.Game):
	def __init__(self):
		base.Game.__init__(self)
		self.client = Client(HOST, PORT)
		self.title = "Multiplayer game (%s:%s)" % (HOST, PORT)
		self.show_fps = False
		self.username = "wg4568"
		self.color = (255, 0, 0)
		self.direction = 0

		self.client.connect()
		self.client.info("color", "%s %s %s" % (self.color[0], self.color[1], self.color[2]))
		self.client.info("username", self.username)

	def logic(self):
		self.client.checkin()
		self.client.get()

	def control(self, keys, mouse):
		if keys[self.pygame.K_UP]: # 0: up  1: right  2: down  3: left
			self.direction = 0
			self.client.update(self.direction)
		if keys[self.pygame.K_RIGHT]:
			self.direction = 1
			self.client.update(self.direction)
		if keys[self.pygame.K_DOWN]:
			self.direction = 2
			self.client.update(self.direction)
		if keys[self.pygame.K_LEFT]:
			self.direction = 3
			self.client.update(self.direction)

	def draw(self):
		for client in self.client.clients:
			x = (client[0])*10
			y = (50-client[1])*10
			col = client[2]
			self.draw_rect(self.screen, col, [x, y, 10, 10])

	def on_stop(self):
		self.client.disconnect()
		self.client.sock.close()

game = Game()
game.run()