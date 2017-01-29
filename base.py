import pygame, time
pygame.M_1 = 323
pygame.M_2 = 324
pygame.M_3 = 325

def control_check():
	keys = list(pygame.key.get_pressed())
	mouse = pygame.mouse.get_pressed()
	keys.append(mouse[0])
	keys.append(mouse[1])
	keys.append(mouse[2])
	return keys

class Game:
	def __init__(self):
		pygame.init()
		self.pygame = pygame

		self.title = "Template Game"
		self.rate = 60
		self.size = [500, 500]
		self.background = (0, 0, 0)
		self.show_fps = True
		self.font = pygame.font.Font('freesansbold.ttf', 12)

		self.events = None

		self.running = False
		self.frame = 0
		self.clock = pygame.time.Clock()

		self.draw_rect = self.pygame.draw.rect
		self.draw_ellipse = self.pygame.draw.ellipse

	def _control(self):
		keys = control_check()
		mouse = pygame.mouse.get_pos()

		try: self.control(keys, mouse)
		except AttributeError: pass

	def _draw(self):
		self.screen.fill(self.background)

		if self.show_fps:
			text = self.font.render("%iFPS" % self.fps, True, (255, 255, 255))
			self.screen.blit(text, (10, 10))

		try: self.draw()
		except AttributeError: pass

	def _logic(self):		
		try: self.logic()
		except AttributeError: pass

	def text(self, txt, posn, col):
			text = self.font.render(txt, True, col)
			self.screen.blit(text, posn)

	def r(self, d, p):
		if d == "x":
			return self.size[0] - p
		else:
			return self.size[1] - p

	def stop(self):
		self.running = False
		try: self.on_stop()
		except AttributeError: pass

	def run(self):
		self.screen = pygame.display.set_mode(self.size)
		pygame.display.set_caption(self.title)

		self.running = True
		self.fps = 0
		fps_time_counter = time.time()
		fps_counter = 0

		while self.running:
			fps_counter += 1
			if time.time()-fps_time_counter >= 0.5:
				fps_time_counter = time.time()
				self.fps = fps_counter*2
				fps_counter = 0

			self.events = self.pygame.event.get()

			self.frame += 1
			for event in self.events:
				if event.type == pygame.QUIT:
					self.stop()

			self._logic()
			self._control()
			self._draw()

			pygame.display.update()
			self.clock.tick(self.rate)