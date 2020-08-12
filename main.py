# Super Shooter Defender 2019, an educational game by Zachary Picone
# Based on a PyGame example program by 'kidscancode', available on their GitHub
# Sprites from Kenney.nl under the CC0 license
# Copyright (C) 2019 Zachary Picone
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# If needed, I can be contacted at zacharypicone@gmail.com.

import pygame as pg
import sys
from os import path
from settings import *
from sprites import *
from tilemap import *

# HUD functions
def draw_player_health(surf, x, y, pct):
	if pct < 0:
		pct = 0
	BAR_LENGTH = 100
	BAR_HEIGHT = 20
	fill = pct * BAR_LENGTH
	outline_rect = pg.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
	fill_rect = pg.Rect(x, y, fill, BAR_HEIGHT)
	if pct > 0.6:
		col = GREEN
	elif pct > 0.4:
		col = YELLOW
	else:
		col = RED
	pg.draw.rect(surf, col, fill_rect)
	pg.draw.rect(surf, WHITE, outline_rect, 2)

class Game:
	def __init__(self):
		pg.init()
		self.screen = pg.display.set_mode((WIDTH, HEIGHT))
		pg.display.set_caption(TITLE)
		self.clock = pg.time.Clock()
		pg.key.set_repeat(500, 100)
		self.load_data()

	def load_data(self):
		game_folder = path.dirname(__file__)
		img_folder = path.join(game_folder, 'assets')
		map_folder = path.join(game_folder, 'tileset')
		snd_folder = path.join(game_folder, 'snd')
		music_folder = path.join(snd_folder, 'music')
		self.map = TiledMap(path.join(map_folder, 'lvl1.tmx'))
		# Loading in all image assets used
		self.map_img = self.map.make_map()
		self.map_rect =	self.map_img.get_rect()
		self.player_img = pg.image.load(path.join(img_folder, PLAYER_IMG)).convert_alpha()
		self.mob_img = pg.image.load(path.join(img_folder, MOB_IMG)).convert_alpha()
		self.fist_img = pg.image.load(path.join(img_folder, FIST_IMG)).convert_alpha()
		self.fist_img = pg.transform.scale(self.fist_img, (TILESIZE, TILESIZE))
		self.wall_img = pg.image.load(path.join(img_folder, WALL_IMG)).convert_alpha()
		self.wall_img = pg.transform.scale(self.wall_img, (TILESIZE, TILESIZE)) # Resizes image to correct size
		self.death_particles = []
		for img in BLOOD_PARTICLES:
			self.death_particles.append(pg.image.load(path.join(img_folder, img)).convert_alpha())
		self.item_images = {}
		for item in ITEM_IMAGES:
			self.item_images[item] = pg.image.load(path.join(img_folder, ITEM_IMAGES[item])).convert_alpha()
		# Sound loading
		pg.mixer.music.load(path.join(music_folder, BG_MUSIC))
		self.effects_sounds = {}
		for type in EFFECTS_SOUNDS:
			self.effects_sounds[type] = pg.mixer.Sound(path.join(snd_folder, EFFECTS_SOUNDS[type]))
		self.weapon_sounds = {}
		self.weapon_sounds['punch'] = []
		for snd in WEAPON_SOUNDS_PUNCH:
			s = pg.mixer.Sound(path.join(snd_folder, snd))
			s.set_volume(0.7)
			self.weapon_sounds['punch'].append(s)
		self.enemy_death_sounds = []
		for snd in ENEMY_DEATH_SOUND:
			self.enemy_death_sounds.append(pg.mixer.Sound(path.join(snd_folder, snd)))
		self.death_sounds = []
		for snd in DEATH_SOUND:
			self.death_sounds.append(pg.mixer.Sound(path.join(snd_folder, snd)))
		self.enemy_hit_sounds = []
		for snd in ENEMY_HIT_SOUND:
			self.enemy_hit_sounds.append(pg.mixer.Sound(path.join(snd_folder, snd)))

	def new(self):
		# initialize all variables and do all the setup for a new game
		self.all_sprites = pg.sprite.LayeredUpdates()
		self.walls = pg.sprite.Group()
		self.mobs = pg.sprite.Group()
		self.fists = pg.sprite.Group()
		self.items = pg.sprite.Group()
		#	for row, tiles in enumerate(self.map.data):
		#		for col, tile in enumerate(tiles):
		#			if tile == '1':
		#				Wall(self, col, row)
		#			if tile == 'M':
		#				Mob(self, col, row)
		#			if tile == 'P':
		#				self.player = Player(self, col, row)
		for tile_object in self.map.tmxdata.objects:
			obj_center = vec(tile_object.x + tile_object.width / 2,
							 tile_object.y + tile_object.height / 2)
			if tile_object.name == 'player':
				self.player = Player(self, obj_center.x, obj_center.y)
			if tile_object.name == 'thug':
				Mob(self, obj_center.x, obj_center.y)
			if tile_object.name == 'wall':
				Obstacle(self, tile_object.x, tile_object.y, tile_object.width, tile_object.height)
			if tile_object.name in ['health']:
				Item(self, obj_center, tile_object.name)
		self.camera = Camera(self.map.width, self.map.height)
		self.draw_debug = False
		# self.effects_sounds['level_start'].play()

	def run(self):
		# game loop - set self.playing = False to end the game
		self.playing = True
		pg.mixer.music.set_volume(0.5)
		pg.mixer.music.play(loops=-1)
		while self.playing:
			self.dt = self.clock.tick(FPS) / 1000.0 # fix for Python 2.x, not needed but still useful
			self.events()
			self.update()
			self.draw()

	def quit(self):
		pg.quit()
		sys.exit()

	def update(self):
		# update portion of the game loop
		self.all_sprites.update()
		self.camera.update(self.player)
		# player hits items
		hits = pg.sprite.spritecollide(self.player, self.items, False)
		for hit in hits:
			if hit.type == 'health' and self.player.health < PLAYER_HEALTH:
				hit.kill()
				self.effects_sounds['health_up'].play()
				self.player.add_health(HEALTH_PACK_AMOUNT)
		# mobs hit player // TODO: replace mobs with bullets here
		hits = pg.sprite.spritecollide(self.player, self.mobs, False, collide_hit_rect)
		for hit in hits:
			self.player.health -= MOB_DAMAGE
			choice(self.enemy_hit_sounds).play()
			hit.vel = vec(0, 0)
			if self.player.health <= 0:
				choice(self.enemy_death_sounds).play()
				self.playing = False
		if hits:
			self.player.pos += vec(MOB_KNOCKBACK, 0).rotate(-hits[0].rot)
		# punches hit enemies
		hits = pg.sprite.groupcollide(self.mobs, self.fists, False, False)
		for hit in hits:
			hit.health -= FIST_DAMAGE
			hit.vel = vec(100, 100) # I MADE THEM GO BACK

			# this is utterly fucked
			# a grave transgression has been made in the
			# creation of this code

	def draw_grid(self): # Draws tile grid over the screen
		for x in range(0, WIDTH, TILESIZE):
			pg.draw.line(self.screen, BROWN, (x, 0), (x, HEIGHT))
		for y in range(0, HEIGHT, TILESIZE):
			pg.draw.line(self.screen, BROWN, (0, y), (WIDTH, y))

	def draw(self):
		pg.display.set_caption("{:.2f}".format(self.clock.get_fps())) # shows fps in title bar for optimisation purposes
		# self.screen.fill(BGCOLOR)
		# self.draw_grid() // draws grid over the gameplay area
		self.screen.blit(self.map_img, self.camera.apply_rect(self.map_rect))
		for sprite in self.all_sprites:
			if isinstance(sprite, Mob):
				sprite.draw_health()
			self.screen.blit(sprite.image, self.camera.apply(sprite))
			if self.draw_debug:
				pg.draw.rect(self.screen, GREEN, self.camera.apply_rect(sprite.hit_rect), 1)
		if self.draw_debug:
			for wall in self.walls:
				pg.draw.rect(self.screen, CYAN, self.camera.apply_rect(wall.rect), 1)
		# pg.draw.rect(self.screen, WHITE, self.player.hit_rect, 2) # Shows hitbox of player
		# HUD functions
		draw_player_health(self.screen, 10, 10, self.player.health / PLAYER_HEALTH)
		pg.display.flip()

	def events(self):
		# catch all events here
		for event in pg.event.get():
			if event.type == pg.QUIT:
				self.quit()
			if event.type == pg.KEYDOWN:
				if event.key == pg.K_ESCAPE:
					self.quit()
				if event.key == pg.K_i:
					self.draw_debug = not self.draw_debug

	def show_start_screen(self):
		pass

	def show_go_screen(self):
		pass

# create the game object
g = Game()
g.show_start_screen()
while True:
	g.new()
	g.run()
	g.show_go_screen()
