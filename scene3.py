#--- scene2.py ---
import arcade
import os
import time
from main import MainView
from main import start_time

import random

# Scene module for graphics, assets and logic
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Paths used by this scene (adjust per scene file)
WALK_FRAMES_FOLDER = "assets/sprites/Demon/walk"
ATTACK_FRAMES_FOLDER = "assets/sprites/Demon/attack"
FOLLOWER_WALK_FOLDER = "assets/sprites/Hero/walk1"
FOLLOWER_FRAMES_FOLDER = "assets/sprites/Hero/idle"
FOLLOWER_ATTACK_FRAMES_FOLDER = "assets/sprites/Hero/attack2"
TILE_SCALING = 1.48
MAP_FILE = "Tileset/Maps/Last_Map.tmx"
FOLLOWER_SPEED = 1.5

# Constantes pour le système de propulsion et charge
KNOCKBACK_FORCE = 10
KNOCKBACK_DISTANCE = 270
FOLLOWER_CHARGE_SPEED = 3
CHARGE_COOLDOWN_MIN = 3.0
CHARGE_COOLDOWN_MAX = 3.0
CHARGE_DISTANCE = 200

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
        self.player_health = 100
        self.player_max_health = self.player_health
        self.hero_health = 100
        self.hero_max_health = self.hero_health
        self.player_attack_damage = 1
        self.follower_attack_damage = 1
        self.player_dealt_damage = False

        # Système de charge du héros
        self.follower_charging = False
        self.follower_charge_timer = 0
        self.next_charge_time = random.uniform(CHARGE_COOLDOWN_MIN, CHARGE_COOLDOWN_MAX)
        self.charge_cooldown_timer = 0
        self.charge_hit_checked = False

        # Système de propulsion du boss
        self.attack_hit_delay = 0.2
        self.attack_hit_timer = 0
        self.attack_pending = False
        self.follower_hurt = False
        self.follower_hurt_timer = 0

        # Suivi des touches pressées pour éviter les conflits
        self.left_pressed = False
        self.right_pressed = False

        # Scene name
        self.name = 3
        # Name of the next scene module to load when player dies (optional)
        self.next_scene_module = None

    def end_Timer(self,start_time):
        global exec_time
        end_time = time.perf_counter()
        print("Start_Time : ",start_time)
        print("End_time : ",end_time)
        exec_time = end_time - start_time
        exec_time = round(exec_time,2)
        exec_time_min = exec_time / 60
        exec_time_min = round(exec_time_min,2)
        print("Temps total de jeu : ",exec_time_min,"min")
        print("Temps total de jeu : ",exec_time,"sec")


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

        # Create sprites
        self.player_sprite = arcade.Sprite()
        self.player_sprite.textures = self.walk_textures
        if self.walk_textures:
            self.player_sprite.texture = self.walk_textures[0]
        self.player_sprite.center_x = 100
        self.player_sprite.center_y = 600
        self.player_sprite.scale = 1.5
        self.player_sprite.scale_x = -abs(self.player_sprite.scale_x)
        self.player_list.append(self.player_sprite)

        self.follower_sprite = arcade.Sprite()
        self.follower_sprite.textures = self.follower_idle_textures
        if self.follower_idle_textures:
            self.follower_sprite.texture = self.follower_idle_textures[0]
        self.follower_sprite.center_x = 700
        self.follower_sprite.center_y = 600
        self.follower_sprite.scale = 2
        self.follower_sprite.scale_x = -abs(self.follower_sprite.scale_x)
        self.player_list.append(self.follower_sprite)

        # Physics
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite, self.wall_list, gravity_constant=1)
        self.follower_physics = arcade.PhysicsEnginePlatformer(self.follower_sprite, self.wall_list, gravity_constant=1)

    def check_boss_attack_hit(self):
        """Vérifie si l'attaque du boss va toucher le héros (avec délai)"""
        distance = abs(self.player_sprite.center_x - self.follower_sprite.center_x)
        
        # Le boss ne peut pas propulser le héros s'il est en train de charger
        if distance <= KNOCKBACK_DISTANCE and not self.follower_hurt and not self.attack_pending and not self.follower_charging:
            self.attack_pending = True
            self.attack_hit_timer = 0

    def check_follower_charge_hit(self):
        """Vérifie si la charge du héros touche le boss"""
        if not self.charge_hit_checked and self.follower_charging:
            distance = abs(self.player_sprite.center_x - self.follower_sprite.center_x)
            
            if distance <= CHARGE_DISTANCE:
                self.charge_hit_checked = True
                
                # Dégâts doublés pendant la charge
                self.player_health -= self.follower_attack_damage * 2
                if self.player_health <= 0:
                    try:
                        self.player_sprite.kill()
                    except Exception:
                        pass
                
                # Arrêter la charge après impact
                self.follower_charging = False
                self.follower_charge_timer = 0
                self.follower_sprite.change_x = 0
                # Remettre les textures par défaut après impact
                self.follower_sprite.textures = self.follower_idle_textures
                if self.follower_idle_textures:
                    self.follower_sprite.texture = self.follower_idle_textures[0]

    def start_follower_charge(self):
        """Démarre l'attaque de charge du héros"""
        if not self.follower_hurt and not self.follower_charging and self.hero_health > 0:
            # Arrêter l'attaque en cours pour lancer la charge
            if self.follower_attacking:
                self.follower_attacking = False
                self.follower_attack_frame = 0
                self.follower_attack_timer = 0
            
            self.follower_charging = True
            self.follower_charge_timer = 0
            self.charge_hit_checked = False
            self.follower_frame = 0
            
            # Changer vers les textures d'attaque pour la charge (attack2)
            self.follower_sprite.textures = self.follower_attack_textures
            if self.follower_attack_textures:
                self.follower_sprite.texture = self.follower_attack_textures[0]
            
            # Déterminer la direction de la charge (vers le boss)
            if self.player_sprite.center_x > self.follower_sprite.center_x:
                self.follower_sprite.change_x = FOLLOWER_CHARGE_SPEED
            else:
                self.follower_sprite.change_x = -FOLLOWER_CHARGE_SPEED

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
        if not self.follower_charging:  # Pas de dégâts pendant la charge
            self.player_health -= self.follower_attack_damage
            if self.player_health <= 0:
                try:
                    self.player_sprite.kill()
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

        # Système de charge aléatoire du héros
        if not self.follower_charging and not self.follower_hurt and self.hero_health > 0:
            self.charge_cooldown_timer += delta_time
            if self.charge_cooldown_timer >= self.next_charge_time:
                self.start_follower_charge()
                self.charge_cooldown_timer = 0
                self.next_charge_time = random.uniform(CHARGE_COOLDOWN_MIN, CHARGE_COOLDOWN_MAX)

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
                    if self.current_frame == 8 and not self.player_dealt_damage:
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
                
                # Vérifier si le héros est toujours vulnérable (pas en charge)
                if not self.follower_charging:
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
                    if self.hero_health <= 0:
                        try:
                            self.follower_sprite.kill()
                        except Exception:
                            pass

        # Follower logic
        if self.follower_charging:
            # Animation de charge (utilise attack2)
            if self.follower_attack_textures:
                self.follower_timer += delta_time
                if self.follower_timer > 0.1:
                    self.follower_frame = (self.follower_frame + 1) % len(self.follower_attack_textures)
                    self.follower_sprite.texture = self.follower_attack_textures[self.follower_frame]
                    self.follower_timer = 0
            
            # Vérifier si la charge touche le boss
            self.check_follower_charge_hit()
            
            # Arrêter la charge après un certain temps ou si on s'éloigne trop
            self.follower_charge_timer += delta_time
            distance_to_boss = abs(self.player_sprite.center_x - self.follower_sprite.center_x)
            
            if self.follower_charge_timer > 5.0 or distance_to_boss > CHARGE_DISTANCE * 2.0:
                self.follower_charging = False
                self.follower_charge_timer = 0
                self.follower_sprite.change_x = 0
                # Remettre les textures par défaut après la charge
                self.follower_sprite.textures = self.follower_idle_textures
                if self.follower_idle_textures:
                    self.follower_sprite.texture = self.follower_idle_textures[0]

        elif self.follower_hurt:
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
            # Comportement normal : suivre le boss (utilise logique du fichier 1)
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

    def on_key_press(self, key, modifiers):
        # Le boss ne peut pas bouger si le héros charge
        if self.follower_charging:
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
                print("Fin du jeu")
                arcade.exit()
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
        # Le boss ne peut pas s'arrêter si le héros charge (il reste figé)
        if self.follower_charging:
            return
            
        if key == arcade.key.LEFT:
            self.left_pressed = False
            if not self.right_pressed:
                self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT:
            self.right_pressed = False
            if not self.left_pressed:
                self.player_sprite.change_x = 0