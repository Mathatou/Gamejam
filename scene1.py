#--- scene2.py ---
import arcade
import os
import random
import math

# Scene module for graphics, assets and logic
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Paths used by this scene (adjust per scene file)
WALK_FRAMES_FOLDER = "assets/sprites/Monster_1/walk"
ATTACK_FRAMES_FOLDER = "assets/sprites/Monster_1/attack"
FOLLOWER_WALK_FOLDER = "assets/sprites/Hero/walk1"
FOLLOWER_FRAMES_FOLDER = "assets/sprites/Hero/idle"
FOLLOWER_ATTACK_FRAMES_FOLDER = "assets/sprites/Hero/attack2"
TILE_SCALING = 1.48
MAP_FILE = "./Tileset/Maps/First_map.tmx"
FOLLOWER_SPEED = 1.5

# Clignotement du joueur : si player_health < BLINK_HEALTH_THRESHOLD -> clignoter
BLINK_HEALTH_THRESHOLD = 5
BLINK_INTERVAL = 0.15

# Particules
PARTICLE_DEFAULT_COUNT = 18
PARTICLE_MIN_SPEED = 1.0
PARTICLE_MAX_SPEED = 3.0
PARTICLE_MIN_LIFE = 0.4
PARTICLE_MAX_LIFE = 1.0

class Scene:
    # Dialogues for scene 1 (English, short)
    dialogues = [
        "Hero : What is this weird monster?! I didn’t even get to warm up.",
        "Hero : This will serve as training!",
        "Mushdoom : Blergh shwoop-shwoop! Shipidiko toxicoatak!",
        "Mushdoom : (You fucker! I’m gonna crush you, Toxic Attack!)",
    ]
    dialogue_index = 0
    dialogue_active = True
    """Encapsule les assets graphiques, sons, logique et interfaces draw/update/inputs."""
    def __init__(self):
        # Visuals
        self.background_texture = None

        # Sounds
        self.boss_attack_sound = None
        self.follower_attack_sound = None
        self.background_music = None

        # Sprites & lists
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.player_sprite = None
        self.follower_sprite = None
        self.tile_map = None

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

        # Clignotement du player (état)
        self.player_blink_timer = 0.0
        self.player_blink_visible = True
        self.blink_interval = BLINK_INTERVAL

        # Particules
        try:
            self.particle_texture = arcade.make_circle_texture(6, arcade.color.ALIZARIN_CRIMSON)
        except Exception:
            self.particle_texture = None
        self.particle_list = arcade.SpriteList()

        # Scene name
        self.name=1
        # Name of the next scene module to load when player dies (optional)
        self.next_scene_module = "scene2"

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

        # Background image
        try:
            self.background_texture = arcade.load_texture(":resources:images/backgrounds/stars.png")
        except Exception:
            self.background_texture = None

        # Tilemap / ground
        try:
            self.tile_map = arcade.load_tilemap(MAP_FILE, scaling=TILE_SCALING)
            print(MAP_FILE)
            self.wall_list = self.tile_map.sprite_lists.get('Platforms') or self.tile_map.sprite_lists.get('Ground') or arcade.SpriteList()
        except Exception:
            self.wall_list = arcade.SpriteList()

        # Load frames
        self.walk_textures = self.load_frames(WALK_FRAMES_FOLDER)
        self.attack_textures = self.load_frames(ATTACK_FRAMES_FOLDER)[1:]
        self.follower_idle_textures = self.load_frames(FOLLOWER_FRAMES_FOLDER)
        self.follower_walk_textures = self.load_frames(FOLLOWER_WALK_FOLDER)
        self.follower_attack_textures = self.load_frames(FOLLOWER_ATTACK_FRAMES_FOLDER)
        if not self.follower_attack_textures:
            self.follower_attack_textures = self.follower_idle_textures.copy()

        # Create sprites
        self.player_sprite = arcade.Sprite()
        self.player_sprite.textures = self.walk_textures
        if self.walk_textures:
            self.player_sprite.texture = self.walk_textures[0]
        self.player_sprite.center_x =  600
        self.player_sprite.center_y =  600
        self.player_sprite.scale = 2.0
        self.player_sprite.scale_x = -abs(self.player_sprite.scale_x)
        self.player_list.append(self.player_sprite)

        self.follower_sprite = arcade.Sprite()
        self.follower_sprite.textures = self.follower_idle_textures
        if self.follower_idle_textures:
            self.follower_sprite.texture = self.follower_idle_textures[0]
        self.follower_sprite.center_x =  100
        self.follower_sprite.center_y =  600
        self.follower_sprite.scale = 2.0
        self.follower_sprite.scale_x = -abs(self.follower_sprite.scale_x)
        self.player_list.append(self.follower_sprite)

        # Physics
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite, self.wall_list, gravity_constant=1)
        self.follower_physics = arcade.PhysicsEnginePlatformer(self.follower_sprite, self.wall_list, gravity_constant=1)

    def spawn_particles(self, x, y, count=PARTICLE_DEFAULT_COUNT):
        """Crée des particules simples autour de (x,y)."""
        if self.particle_texture is None:
            return
        for _ in range(count):
            p = arcade.Sprite()
            p.texture = self.particle_texture
            p.center_x = x + random.uniform(-6, 6)
            p.center_y = y + random.uniform(-6, 6)
            speed = random.uniform(PARTICLE_MIN_SPEED, PARTICLE_MAX_SPEED)
            angle = random.uniform(0, 2 * math.pi)
            p.vx = math.cos(angle) * speed
            p.vy = math.sin(angle) * speed * 0.8
            p.max_life = random.uniform(PARTICLE_MIN_LIFE, PARTICLE_MAX_LIFE)
            p.life = p.max_life
            p.alpha = 255
            p.scale = random.uniform(0.6, 1.2)
            self.particle_list.append(p)

    def on_draw(self):
        # Draw background
        if self.background_texture:
          arcade.draw_texture_rect(
                self.background_texture,
                arcade.XYWH(
                    SCREEN_WIDTH / 2,
                    SCREEN_HEIGHT / 2,
                    SCREEN_WIDTH,
                    SCREEN_HEIGHT
                )
            )
        if self.tile_map:
            for layer in self.tile_map.sprite_lists.values():
                layer.draw()

        # Draw layers
        self.wall_list.draw()
        self.player_list.draw()

        # draw particles (au-dessus des sprites pour effet visible)
        self.particle_list.draw()

        # Health bars
        hb_w, hb_h = 50, 10
        hx = self.player_sprite.center_x - hb_w//2
        hy = self.player_sprite.center_y + self.player_sprite.height//4
        arcade.draw_lbwh_rectangle_filled(hx, hy, hb_w, hb_h, arcade.color.GRAY)
        hp_p = self.player_health / max(1, self.player_max_health)
        arcade.draw_lbwh_rectangle_filled(hx, hy, hb_w * hp_p, hb_h, arcade.color.GREEN if hp_p > 0.3 else arcade.color.RED)

        # Hero bar
        hero_w, hero_h = 40, 8
        hx2 = self.follower_sprite.center_x - hero_w//2
        hy2 = self.follower_sprite.center_y + self.follower_sprite.height//4
        arcade.draw_lbwh_rectangle_filled(hx2, hy2, hero_w, hero_h, arcade.color.GRAY)
        hero_p = max(0.0, min(1.0, (self.hero_health / max(1, self.hero_max_health))))
        arcade.draw_lbwh_rectangle_filled(hx2, hy2, hero_w * hero_p, hero_h, arcade.color.GREEN if hero_p > 0.3 else arcade.color.RED)

        # Display current dialogue (smaller font)
        if self.dialogue_active:
            text = self.dialogues[self.dialogue_index]
            arcade.draw_text(text, 35, 40, arcade.color.WHITE, 14, width=580, align="left")
            arcade.draw_text("Press SPACE to continue...", 35, 10, arcade.color.LIGHT_GRAY, 12)

    def on_update(self, delta_time):
        if self.dialogue_active:
            return
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
        min_distance = 110
        if self.player_health > 0 and not self.follower_attacking:
            if abs(dx) > min_distance:
                self.follower_sprite.change_x = FOLLOWER_SPEED if dx > 0 else -FOLLOWER_SPEED
            else:
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
            self.player_sprite.scale_x = abs(self.player_sprite.scale_x)
            self.follower_sprite.scale_x = abs(self.follower_sprite.scale_x)
        else:
            self.player_sprite.scale_x = -abs(self.player_sprite.scale_x)
            self.follower_sprite.scale_x = -abs(self.follower_sprite.scale_x)

        # Clignotement : faire clignoter le joueur si sa vie est strictement inférieure au seuil
        if self.player_sprite:
            if 0 < self.player_health < BLINK_HEALTH_THRESHOLD:
                self.player_blink_timer += delta_time
                if self.player_blink_timer > self.blink_interval:
                    self.player_blink_visible = not self.player_blink_visible
                    self.player_sprite.alpha = 255 if self.player_blink_visible else 0
                    self.player_blink_timer = 0.0
            else:
                # s'assurer que le sprite est visible quand la condition n'est plus vraie
                if getattr(self.player_sprite, 'alpha', 255) != 255:
                    self.player_sprite.alpha = 255
                self.player_blink_timer = 0.0
                self.player_blink_visible = True

        # Mettre à jour les particules (position, gravité simple, alpha)
        if len(self.particle_list) > 0:
            remove_list = []
            for p in self.particle_list:
                p.center_x += getattr(p, 'vx', 0)
                p.center_y += getattr(p, 'vy', 0)
                p.vy -= 0.12  # légère gravité
                p.life -= delta_time
                if p.life <= 0:
                    remove_list.append(p)
                else:
                    try:
                        p.alpha = int(255 * (p.life / max(0.0001, p.max_life)))
                    except Exception:
                        p.alpha = 255
            for p in remove_list:
                p.remove_from_sprite_lists()

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
        # spawn particules quand le joueur est touché
        try:
            self.spawn_particles(self.player_sprite.center_x, self.player_sprite.center_y, count=12)
        except Exception:
            pass
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
        # Advance dialogue with SPACE, start fight after last
        if self.dialogue_active and key == arcade.key.SPACE:
            self.dialogue_index += 1
            if self.dialogue_index >= len(self.dialogues):
                self.dialogue_active = False
            return
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
