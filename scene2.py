#--- scene2.py ---
import arcade
import os
import random
import math

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

# Constantes pour le système de propulsion
KNOCKBACK_FORCE = 5
KNOCKBACK_DISTANCE = 165


TILE_SCALING = 1.48
MAP_FILE = "Tileset/Maps/Second_Map.tmx"
FOLLOWER_SPEED = 1.7

# --- Clignotement ---
BLINK_HEALTH_THRESHOLD = 5   # si player_health < 5 -> clignoter
BLINK_INTERVAL = 0.15        # secondes entre alternances

# Particules
PARTICLE_DEFAULT_COUNT = 18
PARTICLE_MIN_SPEED = 1.0
PARTICLE_MAX_SPEED = 3.0
PARTICLE_MIN_LIFE = 0.4
PARTICLE_MAX_LIFE = 1.0

# Pluie (ambiance)
RAIN_SPAWN_RATE = 80          # gouttes par seconde (moyenne)
RAIN_MIN_SPEED = 3.0
RAIN_MAX_SPEED = 7.0
RAIN_WIDTH = 2
RAIN_HEIGHT = 12
RAIN_COLOR = arcade.color.LIGHT_GRAY

class Scene:
    # Dialogues for scene 2 (English, short, with character names)
    dialogues = [
        "Narrator: 10 minutes later...",
        "Hero: After so much effort... I finally face the entrance of the demon's castle...",
        "Hero: Is this the last guardian of the lord of this realm?",
        "Skeleton: Skrrrklonk... shaka-shaka? (You think I’m cracking under the pressure?)",
        "Skeleton: Brrrzzzt-kloklok! (I'm just cracking my bones!)",
    ]
    dialogue_index = 0
    dialogue_active = True
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

        # Pluie (ambiance)
        try:
            # essai texture fine verticale si disponible
            self.rain_texture = arcade.make_soft_square_texture(RAIN_HEIGHT, RAIN_COLOR)
        except Exception:
            try:
                self.rain_texture = arcade.make_circle_texture(4, RAIN_COLOR)
            except Exception:
                self.rain_texture = None
        self.rain_list = arcade.SpriteList()
        self.rain_accumulator = 0.0
        self.rain_spawn_rate = RAIN_SPAWN_RATE

        # Scene name
        self.name=2
        # Name of the next scene module to load when player dies (optional)
        self.next_scene_module = "scene3"

        # Knockback system (propulsion)
        self.attack_hit_delay = 0.3
        self.attack_hit_timer = 0
        self.attack_pending = False
        self.follower_hurt = False
        self.follower_hurt_timer = 0

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
        self.player_sprite.center_x =  700
        # reasonable vertical position on the map
        self.player_sprite.center_y =  200
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
        self.follower_sprite.center_x =  100
        self.follower_sprite.center_y =  200
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

    def spawn_rain(self, x=None, y=None, count=1):
        """Crée 'count' gouttes de pluie réparties en haut de l'écran (x/y None -> positions aléatoires)."""
        if self.rain_texture is None:
            return
        for _ in range(count):
            r = arcade.Sprite()
            r.texture = self.rain_texture
            # spawn across the screen if x is None
            r.center_x = random.uniform(0, SCREEN_WIDTH) if x is None else (x + random.uniform(-20, 20))
            r.center_y = SCREEN_HEIGHT + random.uniform(0, 40) if y is None else y + random.uniform(-4, 4)
            speed = random.uniform(RAIN_MIN_SPEED, RAIN_MAX_SPEED)
            r.vx = random.uniform(-0.5, 0.5)  # slight wind
            r.vy = -speed
            r.alpha = 180
            # adjust scale so small thin drops are plausible
            tex_w = getattr(self.rain_texture, 'width', RAIN_WIDTH)
            r.scale = (RAIN_WIDTH / max(1, tex_w))
            self.rain_list.append(r)

    def on_draw(self):
        # Draw layers
        if self.tile_map:
            for layer in self.tile_map.sprite_lists.values():
                layer.draw()

        # draw rain (behind sprites for ambiance)
        self.rain_list.draw()

        self.player_list.draw()

        # draw particles (au-dessus des sprites pour effet visible)
        self.particle_list.draw()

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

        # Display current dialogue (smaller font)
        if self.dialogue_active:
            text = self.dialogues[self.dialogue_index]
            arcade.draw_text(text, 30, 30, arcade.color.WHITE, 14, width=580, align="left")
            arcade.draw_text("Press SPACE to continue...", 30, 10, arcade.color.LIGHT_GRAY, 12)

    def on_update(self, delta_time):
        if self.dialogue_active:
            return
        if self.physics_engine:
            self.physics_engine.update()
        if self.follower_physics:
            self.follower_physics.update()

        # Spawn rain continuously based on spawn rate
        self.rain_accumulator += self.rain_spawn_rate * delta_time
        if self.rain_accumulator >= 1.0:
            to_spawn = int(self.rain_accumulator)
            self.spawn_rain(None, None, count=to_spawn)
            self.rain_accumulator -= to_spawn

        # Update rain positions and remove off-screen
        if len(self.rain_list) > 0:
            remove_r = []
            for r in self.rain_list:
                r.center_x += getattr(r, 'vx', 0)
                r.center_y += getattr(r, 'vy', 0)
                # remove when below screen
                if r.center_y < -20:
                    remove_r.append(r)
            for r in remove_r:
                r.remove_from_sprite_lists()

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
                    # Knockback: déclenchement à la frame d'attaque
                    hit_frame = 1 if len(self.attack_textures) > 1 else 0
                    if self.current_frame == hit_frame and not self.player_dealt_damage:
                        self.check_boss_attack_hit()
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


        # Knockback system (propulsion du follower)
        if self.attack_pending:
            self.attack_hit_timer += delta_time
            if self.attack_hit_timer >= self.attack_hit_delay:
                self.attack_pending = False
                self.follower_hurt = True
                self.follower_hurt_timer = 0
                # Direction knockback
                if self.follower_sprite.center_x < self.player_sprite.center_x:
                    knockback_direction = -1
                else:
                    knockback_direction = 1
                self.follower_sprite.change_x = KNOCKBACK_FORCE * knockback_direction
                # Dégâts
                self.hero_health -= self.player_attack_damage
                # spawn particules au point d'impact du follower
                self.spawn_particles(self.follower_sprite.center_x, self.follower_sprite.center_y, count=20)
                if self.hero_health <= 0:
                    try:
                        self.follower_sprite.kill()
                    except Exception:
                        pass

        if self.follower_hurt:
            self.follower_hurt_timer += delta_time
            if self.follower_hurt_timer > 0.5:
                self.follower_hurt = False
                self.follower_hurt_timer = 0
            # Réduire progressivement la vitesse
            self.follower_sprite.change_x *= 0.95
            if abs(self.follower_sprite.change_x) < 0.5:
                self.follower_sprite.change_x = 0
        else:
            # Follower follow and anim (normal)
            dx = self.player_sprite.center_x - self.follower_sprite.center_x
            dy = self.player_sprite.center_y - self.follower_sprite.center_y
            min_x = 50
            min_y = 10
            if self.player_health > 0 and not self.follower_attacking:
                if abs(dx) > min_x:
                    self.follower_sprite.change_x = FOLLOWER_SPEED if dx > 0 else -FOLLOWER_SPEED
                else:
                    if abs(dy) < min_y:
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

        # Clignotement : faire clignoter le joueur si sa vie est strictement inférieure au seuil
        if self.player_sprite:
            if 0 < self.player_health < BLINK_HEALTH_THRESHOLD:
                self.player_blink_timer += delta_time
                if self.player_blink_timer > self.blink_interval:
                    # alterner visibilité
                    self.player_blink_visible = not self.player_blink_visible
                    # alpha attend une valeur entre 0 et 255
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
                    p.alpha = int(255 * (p.life / max(0.0001, p.max_life)))
            for p in remove_list:
                p.remove_from_sprite_lists()

    def check_boss_attack_hit(self):
        """Vérifie si l'attaque du boss va toucher le héros (avec délai)"""
        distance = abs(self.player_sprite.center_x - self.follower_sprite.center_x)
        if distance <= KNOCKBACK_DISTANCE and not self.follower_hurt and not self.attack_pending:
            self.attack_pending = True
            self.attack_hit_timer = 0

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
        self.spawn_particles(self.player_sprite.center_x, self.player_sprite.center_y, count=12)
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
