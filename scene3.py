#--- scene2.py ---
import arcade
import os
import time
from main import MainView
from main import start_time

import random
import math

# Scene module for graphics, assets and logic
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Paths used by this scene (adjust per scene file)
WALK_FRAMES_FOLDER = "assets/sprites/Demon/walk"
ATTACK_FRAMES_FOLDER = "assets/sprites/Demon/attack"
FOLLOWER_WALK_FOLDER = "assets/sprites/Hero/walk1"
FOLLOWER_FRAMES_FOLDER = "assets/sprites/Hero/idle"
FOLLOWER_ATTACK_FRAMES_FOLDER = "assets/sprites/Hero/attack2"
FIREBALL_SHOOT_FOLDER = "assets/fireballshoot"
FIREBALL_EXPLODE_FOLDER = "assets/fireballexplode"
TILE_SCALING = 1.48
MAP_FILE = "Tileset/Maps/Last_Map.tmx"
FOLLOWER_SPEED = 1.5

LEADERBOARD_FILE = "leaderboard.txt"

# Constantes pour le système de propulsion
KNOCKBACK_FORCE = 7
KNOCKBACK_DISTANCE = 270

# Constantes pour le système de fireball
FIREBALL_SPEED = 5
FIREBALL_DAMAGE = 3
FIREBALL_COOLDOWN = 2.0  # Délai entre les fireballs

# --- Clignotement du joueur ---
BLINK_HEALTH_THRESHOLD = 10
BLINK_INTERVAL = 0.15

# Particules
PARTICLE_DEFAULT_COUNT = 18
PARTICLE_MIN_SPEED = 1.0
PARTICLE_MAX_SPEED = 3.0
PARTICLE_MIN_LIFE = 0.4
PARTICLE_MAX_LIFE = 1.0

class Fireball(arcade.Sprite):
    """Classe pour les projectiles fireball"""
    def __init__(self, shoot_textures, explode_textures):
        super().__init__()
        self.shoot_textures = shoot_textures
        self.explode_textures = explode_textures
        self.current_frame = 0
        self.frame_timer = 0
        self.exploding = False
        self.target_x = 0
        self.target_y = 0
        self.velocity_x = 0
        self.velocity_y = 0
        
        if shoot_textures:
            self.texture = shoot_textures[0]
            self.textures = shoot_textures
    
    def setup_trajectory(self, start_x, start_y, target_x, target_y):
        """Configure la trajectoire de la fireball"""
        
        self.center_x = start_x
        self.center_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        
        # Calculer la direction
        dx = target_x - start_x
        dy = target_y - start_y
        distance = (dx**2 + dy**2)**0.5
        
        if distance > 0:
            self.velocity_x = (dx / distance) * FIREBALL_SPEED
            self.velocity_y = (dy / distance) * FIREBALL_SPEED
            
            # Calculer l'angle pour orienter le haut de l'image vers la direction
            angle_rad = math.atan2(dy, dx)
            self.angle = math.degrees(angle_rad) + 90
    
    def update_animation(self, delta_time):
        """Met à jour l'animation de la fireball"""
        self.frame_timer += delta_time
        
        if self.exploding:
            if self.frame_timer > 0.1:
                self.current_frame += 1
                if self.current_frame >= len(self.explode_textures):
                    return True  # Animation d'explosion terminée
                else:
                    self.texture = self.explode_textures[self.current_frame]
                self.frame_timer = 0
        else:
            if self.frame_timer > 0.1:
                self.current_frame = (self.current_frame + 1) % len(self.shoot_textures)
                self.texture = self.shoot_textures[self.current_frame]
                self.frame_timer = 0
        
        return False
    
    def start_explosion(self):
        """Démarre l'animation d'explosion"""
        self.exploding = True
        self.current_frame = 0
        self.textures = self.explode_textures
        self.velocity_x = 0
        self.velocity_y = 0
        if self.explode_textures:
            self.texture = self.explode_textures[0]

class Scene:
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
        self.fireball_list = arcade.SpriteList()
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
        
        # Fireball animations
        self.fireball_shoot_textures = []
        self.fireball_explode_textures = []

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
        self.player_health = 45
        self.player_max_health = self.player_health
        self.hero_health = 100
        self.hero_max_health = self.hero_health
        self.player_attack_damage = 1
        self.follower_attack_damage = 1
        self.player_dealt_damage = False

        # Système de propulsion du boss
        self.attack_hit_delay = 0.2
        self.attack_hit_timer = 0
        self.attack_pending = False
        self.follower_hurt = False
        self.follower_hurt_timer = 0

        # Suivi des touches pressées pour éviter les conflits
        self.left_pressed = False
        self.right_pressed = False

        # Système de fireball
        self.fireball_cooldown_timer = 0
        self.fireball_list = arcade.SpriteList()

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
        self.name = 3
        # Name of the next scene module to load when player dies (optional)
        self.next_scene_module = None

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
        
        # Load fireball animations
        self.fireball_shoot_textures = self.load_frames(FIREBALL_SHOOT_FOLDER)
        self.fireball_explode_textures = self.load_frames(FIREBALL_EXPLODE_FOLDER)

        # Create sprites
        self.player_sprite = arcade.Sprite()
        self.player_sprite.textures = self.walk_textures
        if self.walk_textures:
            self.player_sprite.texture = self.walk_textures[0]



        self.player_sprite.center_x = 650

        self.player_sprite.center_y = 600
        self.player_sprite.scale = 1.4
        self.player_sprite.scale_x = -abs(self.player_sprite.scale_x)
        self.player_list.append(self.player_sprite)

        self.follower_sprite = arcade.Sprite()
        self.follower_sprite.textures = self.follower_idle_textures
        if self.follower_idle_textures:
            self.follower_sprite.texture = self.follower_idle_textures[0]
        self.follower_sprite.center_x = 100
        self.follower_sprite.center_y = 600
        self.follower_sprite.scale = 2.0
        self.follower_sprite.scale_x = -abs(self.follower_sprite.scale_x)
        self.player_list.append(self.follower_sprite)

        # Physics
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite, self.wall_list, gravity_constant=1)
        self.follower_physics = arcade.PhysicsEnginePlatformer(self.follower_sprite, self.wall_list, gravity_constant=1)

    def check_boss_attack_hit(self):
        """Vérifie si l'attaque du boss va toucher le héros (avec délai)"""
        distance = abs(self.player_sprite.center_x - self.follower_sprite.center_x)
        
        # Le boss peut propulser le héros
        if distance <= KNOCKBACK_DISTANCE and not self.follower_hurt and not self.attack_pending:
            self.attack_pending = True
            self.attack_hit_timer = 0
    
    def end_Timer(self, start_time):
        """Calcule et affiche le temps total de jeu"""
        global exec_time
        end_time = time.perf_counter()
        print("Start_Time : ", start_time)
        print("End_time : ", end_time)
        exec_time = end_time - start_time
        exec_time = round(exec_time, 2)
        exec_time_min = exec_time / 60
        exec_time_min = round(exec_time_min, 2)
        print("Temps total de jeu : ", exec_time_min, "min")
        print("Temps total de jeu : ", exec_time, "sec")

    def create_fireball(self):
        """Crée une nouvelle fireball dirigée vers le boss"""
        if self.fireball_shoot_textures and self.hero_health > 0:
            fireball = Fireball(self.fireball_shoot_textures, self.fireball_explode_textures)
            
            # Position de départ (follower)
            start_x = self.follower_sprite.center_x
            start_y = self.follower_sprite.center_y
            
            # Position cible (quart bas du boss)
            target_x = self.player_sprite.center_x
            target_y = self.player_sprite.center_y - (self.player_sprite.height * 0.375)
            
            # Configurer la trajectoire
            fireball.setup_trajectory(start_x, start_y, target_x, target_y)
            fireball.scale = 3.0
            
            # Ajouter à la liste
            self.fireball_list.append(fireball)
            
            # Reset du cooldown
            self.fireball_cooldown_timer = 0

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
        """Termine l'attaque du follower et inflige des dégâts"""
        self.player_health -= self.follower_attack_damage
        # particules quand le joueur est touché
        try:
            self.spawn_particles(self.player_sprite.center_x, self.player_sprite.center_y, count=12)
        except Exception:
            pass
        if self.player_health <= 0:
            try:
                self.player_sprite.kill()
                print("Fin du jeu - Boss vaincu par le héros")
                self.end_Timer(start_time)
                arcade.exit()
            except Exception:
                pass
        self.follower_attacking = False
        self.follower_attack_frame = 0
        self.follower_attack_timer = 0
        if not self.follower_hurt:
            self.follower_sprite.change_x = 0
        self.follower_sprite.textures = self.follower_idle_textures
        if self.follower_idle_textures:
            self.follower_sprite.texture = self.follower_idle_textures[0]

    def on_draw(self):
        if self.tile_map:
            for layer in self.tile_map.sprite_lists.values():
                layer.draw()

        # Draw layers
        self.wall_list.draw()
        self.player_list.draw()
        self.fireball_list.draw()

        # draw particles (au-dessus des sprites)
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

    def on_update(self, delta_time):
        if self.physics_engine:
            self.physics_engine.update()
        if self.follower_physics:
            self.follower_physics.update()

        # Système de fireball avec cooldown dynamique selon la vie du héros
        self.fireball_cooldown_timer += delta_time
        # Cooldown minimum 0.5s, maximum 2.0s (ajuste selon besoin)
        cooldown = max(0.5, 2.0 * (self.hero_health / max(1, self.hero_max_health)))
        if (self.fireball_cooldown_timer >= cooldown and 
            not self.follower_attacking and 
            self.hero_health > 0 and self.player_health > 0):
            # Lancer une fireball seulement si à distance raisonnable
            distance = abs(self.player_sprite.center_x - self.follower_sprite.center_x)
            if distance > 100:  # Pas trop proche pour éviter le spam
                self.create_fireball()

        # Mise à jour des fireballs
        fireballs_to_remove = []
        for fireball in self.fireball_list:
            # Mouvement de la fireball
            if not fireball.exploding:
                fireball.center_x += fireball.velocity_x
                fireball.center_y += fireball.velocity_y
                
                # Vérifier collision avec le boss (zone du quart bas)
                boss_target_y = self.player_sprite.center_y - (self.player_sprite.height * 0.375)
                if (abs(fireball.center_x - self.player_sprite.center_x) < 30 and
                    abs(fireball.center_y - boss_target_y) < 30):
                    # Collision détectée
                    fireball.start_explosion()
                    # particules à l'impact
                    try:
                        self.spawn_particles(self.player_sprite.center_x, self.player_sprite.center_y, count=14)
                    except Exception:
                        pass
                    self.player_health -= FIREBALL_DAMAGE
                    if self.player_health <= 0:
                        try:
                            self.player_sprite.kill()
                            print("Fin du jeu - Boss vaincu par fireball")
                            self.end_Timer(start_time)
                            arcade.exit()
                        except Exception:
                            pass
                
                # Supprimer si sort de l'écran
                if (fireball.center_x < -50 or fireball.center_x > SCREEN_WIDTH + 50 or
                    fireball.center_y < -50 or fireball.center_y > SCREEN_HEIGHT + 50):
                    fireballs_to_remove.append(fireball)
            
            # Animation
            if fireball.update_animation(delta_time):
                fireballs_to_remove.append(fireball)
        
        # Supprimer les fireballs terminées
        for fireball in fireballs_to_remove:
            fireball.remove_from_sprite_lists()

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
                    hit_frame = 7  # 8e frame (index 7, car on commence à 0)
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

        # Gestion du délai d'attaque du boss (propulsion)
        if self.attack_pending:
            self.attack_hit_timer += delta_time
            if self.attack_hit_timer >= self.attack_hit_delay:
                self.attack_pending = False
                
                # Appliquer la propulsion
                self.follower_hurt = True
                self.follower_hurt_timer = 0
                
                # Calculer la direction et appliquer la propulsion
                if self.follower_sprite.center_x < self.player_sprite.center_x:
                    knockback_direction = -1
                else:
                    knockback_direction = 1
                
                self.follower_sprite.change_x = KNOCKBACK_FORCE * knockback_direction
                
                # Dégâts de propulsion
                self.hero_health -= self.player_attack_damage
                # particules au point d'impact du follower
                try:
                    self.spawn_particles(self.follower_sprite.center_x, self.follower_sprite.center_y, count=20)
                except Exception:
                    pass
                if self.hero_health <= 0:
                    try:
                        self.follower_sprite.kill()
                        print("Fin du jeu - Héros vaincu")
                        self.end_Timer(start_time)
                        arcade.exit()
                    except Exception:
                        pass

        # Follower logic
        if self.follower_hurt:
            # Animation et logique de propulsion
            self.follower_hurt_timer += delta_time
            if self.follower_hurt_timer > 0.5:  # Durée de l'état hurt
                self.follower_hurt = False
                self.follower_hurt_timer = 0
            
            # Réduire progressivement la vitesse de propulsion
            self.follower_sprite.change_x *= 0.95
            if abs(self.follower_sprite.change_x) < 0.5:
                self.follower_sprite.change_x = 0

        else:
            # Comportement normal : suivre le boss
            dx = self.player_sprite.center_x - self.follower_sprite.center_x
            min_distance = 60

            if self.player_health > 0:
                if abs(dx) > min_distance:
                    # Assez loin du boss - arrêter l'attaque et suivre
                    if self.follower_attacking:
                        self.follower_attacking = False
                        self.follower_attack_frame = 0
                        self.follower_attack_timer = 0
                        self.follower_sprite.textures = self.follower_idle_textures
                    
                    self.follower_sprite.change_x = FOLLOWER_SPEED if dx > 0 else -FOLLOWER_SPEED
                else:
                    # Assez proche du boss - déclencher l'attaque si pas déjà en cours
                    if not self.follower_attacking:
                        self.start_follower_attack()
            else:
                # Boss mort - arrêter toute activité
                if self.follower_attacking:
                    self.follower_attacking = False
                self.follower_sprite.change_x = 0

            # Animation de marche normale (seulement si pas en train d'attaquer)
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

        # Animation d'attaque normale du follower
        if self.follower_attacking:
            self.follower_attack_timer += delta_time
            if self.follower_attack_timer > 0.02:
                self.follower_attack_frame += 1
                if self.follower_attack_frame >= len(self.follower_attack_textures):
                    self.finish_follower_attack()
                else:
                    self.follower_sprite.texture = self.follower_attack_textures[self.follower_attack_frame]
                self.follower_attack_timer = 0

        # Réduire progressivement la vitesse du boss (pour l'effet de knockback)
        player_input = self.left_pressed or self.right_pressed
        
        # Ne ralentir que si c'est un knockback et pas un input du joueur
        if abs(getattr(self.player_sprite, 'change_x', 0)) > 0 and not self.attacking and not player_input:
            # Seulement ralentir si la vitesse est élevée (knockback)
            if abs(self.player_sprite.change_x) > 5:
                self.player_sprite.change_x *= 0.9
                if abs(self.player_sprite.change_x) < 0.1:
                    self.player_sprite.change_x = 0

        # Orientation (flip)
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
                p.life = getattr(p, 'life', getattr(p, 'max_life', 0)) - delta_time
                setattr(p, 'life', p.life)
                if p.life <= 0:
                    remove_list.append(p)
                else:
                    try:
                        p.alpha = int(255 * (p.life / max(0.0001, p.max_life)))
                    except Exception:
                        p.alpha = 255
            for p in remove_list:
                p.remove_from_sprite_lists()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP and self.physics_engine and self.physics_engine.can_jump():
            self.player_sprite.change_y = 20
        elif key == arcade.key.LEFT:
            self.left_pressed = True
            self.player_sprite.change_x = -5
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
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
        if key == arcade.key.LEFT:
            self.left_pressed = False
            if not self.right_pressed:
                self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT:
            self.right_pressed = False
            if not self.left_pressed:
                self.player_sprite.change_x = 0

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
