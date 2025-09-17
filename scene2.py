#--- scene2.py ---
import arcade
import os

# Scene module for graphics, assets and logic
# --- Constantes ---
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SCREEN_TITLE = "Plateforme 2D avec map fixe"

# Paths used by this scene (adjust per scene file)

WALK_FRAMES_FOLDER = "assets/sprites/Monster_2/walk"
ATTACK_FRAMES_FOLDER = "assets/sprites/Monster_2/attack2"

FOLLOWER_WALK_FOLDER = "assets/sprites/Hero/walk1"
FOLLOWER_FRAMES_FOLDER = "assets/sprites/Hero/idle"
FOLLOWER_ATTACK_FRAMES_FOLDER = "assets/sprites/Hero/attack2"

TILE_SCALING = 1.48
MAP_FILE = "Tileset/Maps/Second_Map.tmx"
FOLLOWER_SPEED = 1.5

class Scene:
    """Encapsule les assets graphiques, sons, logique et interfaces draw/update/inputs."""
    def __init__(self):
        # Visuals
        self.background_texture = None
        self.tile_map = None
        # Sounds
        self.boss_attack_sound = None
        self.follower_attack_sound = None
        self.background_music = None

        # Sprites & lists
        self.player_list = arcade.SpriteList()
        self.wall_list = None
        self.player_sprite = None
        self.follower_sprite = None

        # Physics
        self.physics_engine = None
        self.follower_physics = None

        # Animations
        self.walk_textures = []
        self.attack_textures = []
        self.follower_idle_textures = []
        self.follower_walk_textures = []
        self.follower_attack_textures = []

        # Animation state
        self.current_frame = 0
        self.frame_timer = 0
        self.attacking = False

        self.follower_frame = 0
        self.follower_timer = 0
        self.follower_attacking = False
        self.follower_attack_frame = 0
        self.follower_attack_timer = 0

        # Health and damage
        self.player_health = 10
        self.player_max_health = self.player_health
        self.hero_health = 100
        self.hero_max_health = self.hero_health
        self.player_attack_damage = 1
        self.follower_attack_damage = 1
        self.player_dealt_damage = False

        # Scene name
        self.name=2
        # Name of the next scene module to load when player dies (optional)
        self.next_scene_module = "scene3"

    def load_frames(self, folder):
        textures = []
        if not os.path.isdir(folder):
            return textures
        files = [f for f in os.listdir(folder) if f.endswith('.png')]
        def extract_number(f):
            name = os.path.splitext(f)[0]
            digits = ''.join(filter(str.isdigit, name))
            return int(digits) if digits != '' else 0
        files.sort(key=extract_number)
        for f in files:
            textures.append(arcade.load_texture(os.path.join(folder, f)))
        return textures

    def setup(self):
        # --- Charger la map ---
        try:
            self.tile_map = arcade.load_tilemap(MAP_FILE, scaling=TILE_SCALING)
        except Exception:
            self.tile_map = None

        # Unifier la récupération du calque sol (Platforms ou Ground)
        if self.tile_map:
            self.wall_list = self.tile_map.sprite_lists.get('Platforms') or self.tile_map.sprite_lists.get('Ground') or arcade.SpriteList()
        else:
            self.wall_list = arcade.SpriteList()

        # Load sounds and music
        try:
            self.boss_attack_sound = arcade.load_sound(":resources:sounds/hit5.wav")
        except Exception:
            self.boss_attack_sound = None
        try:
            self.follower_attack_sound = arcade.load_sound(":resources:sounds/hit4.wav")
        except Exception:
            self.follower_attack_sound = None
        try:
            self.background_music = arcade.load_sound(":resources:music/funkyrobot.mp3")
        except Exception:
            self.background_music = None

        # No background texture for this scene (use tiles from TMX)
        self.background_texture = None

        # Load frames BEFORE creating sprites so textures are available
        self.walk_textures = self.load_frames(WALK_FRAMES_FOLDER)
        frames = self.load_frames(ATTACK_FRAMES_FOLDER)
        self.attack_textures = frames[1:] if len(frames) > 1 else frames
        self.follower_idle_textures = self.load_frames(FOLLOWER_FRAMES_FOLDER)
        self.follower_walk_textures = self.load_frames(FOLLOWER_WALK_FOLDER)
        self.follower_attack_textures = self.load_frames(FOLLOWER_ATTACK_FRAMES_FOLDER)
        if not self.follower_attack_textures:
            self.follower_attack_textures = self.follower_idle_textures.copy()

        # Create player sprite using loaded walk textures (like follower)
        if not self.player_sprite:
            self.player_sprite = arcade.Sprite()
        self.player_sprite.textures = self.walk_textures
        if self.walk_textures:
            self.player_sprite.texture = self.walk_textures[0]
        self.player_sprite.center_x = 100
        # reasonable vertical position on the map
        self.player_sprite.center_y = 200
        self.player_sprite.scale = 2.0
        self.player_sprite.scale_x = -abs(self.player_sprite.scale_x)
        if self.player_sprite not in self.player_list:
            self.player_list.append(self.player_sprite)

        # Create follower sprite
        if not self.follower_sprite:
            self.follower_sprite = arcade.Sprite()
        self.follower_sprite.textures = self.follower_idle_textures
        if self.follower_idle_textures:
            self.follower_sprite.texture = self.follower_idle_textures[0]
        self.follower_sprite.center_x = 700
        self.follower_sprite.center_y = 600
        self.follower_sprite.scale = 2.0
        self.follower_sprite.scale_x = -abs(self.follower_sprite.scale_x)
        if self.follower_sprite not in self.player_list:
            self.player_list.append(self.follower_sprite)

        # Physics: create engines safely using self.wall_list
        try:
            self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite, self.wall_list, gravity_constant=1)
        except Exception:
            self.physics_engine = None
        try:
            self.follower_physics = arcade.PhysicsEnginePlatformer(self.follower_sprite, self.wall_list, gravity_constant=1)
        except Exception:
            self.follower_physics = None

    def on_draw(self):
        # Draw layers
        if self.tile_map:
            for layer in self.tile_map.sprite_lists.values():
                layer.draw()
        self.player_list.draw()

        # Health bars
        if self.player_sprite:
            hb_w, hb_h = 50, 10
            hx = self.player_sprite.center_x - hb_w//2
            hy = self.player_sprite.center_y + (getattr(self.player_sprite, 'height', 0)//4)
            arcade.draw_lbwh_rectangle_filled(hx, hy, hb_w, hb_h, arcade.color.GRAY)
            hp_p = self.player_health / max(1, self.player_max_health)
            arcade.draw_lbwh_rectangle_filled(hx, hy, hb_w * hp_p, hb_h, arcade.color.GREEN if hp_p > 0.3 else arcade.color.RED)

        if self.follower_sprite:
            hero_w, hero_h = 40, 8
            hx2 = self.follower_sprite.center_x - hero_w//2
            hy2 = self.follower_sprite.center_y + (getattr(self.follower_sprite, 'height', 0)//4)
            arcade.draw_lbwh_rectangle_filled(hx2, hy2, hero_w, hero_h, arcade.color.GRAY)
            hero_p = max(0.0, min(1.0, (self.hero_health / max(1, self.hero_max_health))))
            arcade.draw_lbwh_rectangle_filled(hx2, hy2, hero_w * hero_p, hero_h, arcade.color.GREEN if hero_p > 0.3 else arcade.color.RED)

    def on_update(self, delta_time):
        if self.physics_engine:
            self.physics_engine.update()
        if self.follower_physics:
            self.follower_physics.update()

        # Player animation and attack
        if self.attacking:
            self.frame_timer += delta_time
            if self.frame_timer > 0.1:
                self.current_frame += 1
                if self.current_frame >= len(self.attack_textures):
                    self.attacking = False
                    self.current_frame = 0
                    self.player_sprite.textures = self.walk_textures
                else:
                    self.player_sprite.texture = self.attack_textures[self.current_frame]
                    hit_frame = min(1, len(self.attack_textures)-1) if len(self.attack_textures) > 0 else None
                    if hit_frame is not None and self.current_frame == hit_frame and not self.player_dealt_damage:
                        if self.hero_health > 0:
                            self.hero_health -= self.player_attack_damage
                            if self.hero_health <= 0:
                                try:
                                    self.follower_sprite.kill()
                                except Exception:
                                    pass
                        self.player_dealt_damage = True
                self.frame_timer = 0
        else:
            if getattr(self.player_sprite, 'change_x', 0) != 0 and self.walk_textures:
                self.frame_timer += delta_time
                if self.frame_timer > 0.1:
                    self.current_frame = (self.current_frame + 1) % len(self.walk_textures)
                    self.player_sprite.texture = self.walk_textures[self.current_frame]
                    self.frame_timer = 0
            else:
                if self.walk_textures:
                    self.player_sprite.texture = self.walk_textures[0]

        # Follower follow and anim
        dx = self.player_sprite.center_x - self.follower_sprite.center_x
        dy = self.player_sprite.center_y - self.follower_sprite.center_y
        min_x = 50
        min_y = 10
        if self.player_health > 0 and not self.follower_attacking:
            if abs(dx) > min_x:
                self.follower_sprite.change_x = FOLLOWER_SPEED if dx > 0 else -FOLLOWER_SPEED
            else:
                if  abs(dy) < min_y:
                    self.start_follower_attack()
        else:
            self.follower_sprite.change_x = 0

        if not self.follower_attacking:
            if getattr(self.follower_sprite, 'change_x', 0) != 0 and self.follower_walk_textures:
                self.follower_timer += delta_time
                if self.follower_timer > 0.05:
                    self.follower_frame = (self.follower_frame + 1) % len(self.follower_walk_textures)
                    self.follower_sprite.texture = self.follower_walk_textures[self.follower_frame]
                    self.follower_timer = 0
            else:
                if self.follower_idle_textures:
                    self.follower_sprite.texture = self.follower_idle_textures[0]
        else:
            self.follower_attack_timer += delta_time
            if self.follower_attack_timer > 0.02:
                self.follower_attack_frame += 1
                if self.follower_attack_frame >= len(self.follower_attack_textures):
                    self.finish_follower_attack()
                else:
                    self.follower_sprite.texture = self.follower_attack_textures[self.follower_attack_frame]
                self.follower_attack_timer = 0

        # flip
        if self.follower_sprite.center_x < self.player_sprite.center_x:
            self.player_sprite.scale_x = -abs(self.player_sprite.scale_x)
            self.follower_sprite.scale_x = abs(self.follower_sprite.scale_x)
        else:
            self.player_sprite.scale_x = abs(self.player_sprite.scale_x)
            self.follower_sprite.scale_x = -abs(self.follower_sprite.scale_x)

    def start_follower_attack(self):
        if self.player_health <= 0:
            self.follower_attacking = False
            self.follower_sprite.change_x = 0
            return
        self.follower_attacking = True
        self.follower_attack_frame = 0
        self.follower_attack_timer = 0
        self.follower_sprite.change_x = 0
        if self.follower_attack_textures:
            self.follower_sprite.textures = self.follower_attack_textures
            self.follower_sprite.texture = self.follower_attack_textures[0]
        if self.follower_attack_sound:
            arcade.play_sound(self.follower_attack_sound)

    def finish_follower_attack(self):
        self.player_health -= self.follower_attack_damage
        if self.player_health <= 0:
            try:
                self.player_sprite.kill()
            except Exception:
                pass
        self.follower_attacking = False
        self.follower_attack_frame = 0
        self.follower_attack_timer = 0
        self.follower_sprite.change_x = 0
        self.follower_sprite.textures = self.follower_idle_textures
        if self.follower_idle_textures:
            self.follower_sprite.texture = self.follower_idle_textures[0]

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP and self.physics_engine and self.physics_engine.can_jump():
            self.player_sprite.change_y = 20
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -5
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = 5
        elif key == arcade.key.SPACE:
            if not self.attacking and self.player_health > 0:
                self.attacking = True
                self.player_dealt_damage = False
                self.current_frame = 0
                self.player_sprite.textures = self.attack_textures
                if self.attack_textures:
                    self.player_sprite.texture = self.attack_textures[0]
                if self.boss_attack_sound:
                    arcade.play_sound(self.boss_attack_sound)

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0
