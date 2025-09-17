#--- scene2.py ---
import arcade
import os
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

# Constantes pour le système de propulsion et charge
KNOCKBACK_FORCE = 10
KNOCKBACK_DISTANCE = 270
FOLLOWER_CHARGE_SPEED = 3
CHARGE_COOLDOWN_MIN = 3.0
CHARGE_COOLDOWN_MAX = 3.0
CHARGE_DISTANCE = 200

# Constantes pour le système de fireball
FIREBALL_SPEED = 5
FIREBALL_DAMAGE = 3
FIREBALL_COOLDOWN = 2.0  # Délai entre les fireballs

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
            # atan2 donne l'angle en radians, on le convertit en degrés
            angle_rad = math.atan2(dy, dx)
            # On ajoute 90° car l'image pointe vers le haut par défaut (0°)
            # et on veut qu'elle pointe dans la direction du mouvement
            self.angle = math.degrees(angle_rad) - 90
    
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

        # Système de fireball
        self.fireball_cooldown_timer = 0
        self.fireball_list = arcade.SpriteList()

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
        self.player_sprite.center_x = 100
        self.player_sprite.center_y = 600
        self.player_sprite.scale = 1.4
        self.player_sprite.scale_x = -abs(self.player_sprite.scale_x)
        self.player_list.append(self.player_sprite)

        self.follower_sprite = arcade.Sprite()
        self.follower_sprite.textures = self.follower_idle_textures
        if self.follower_idle_textures:
            self.follower_sprite.texture = self.follower_idle_textures[0]
        self.follower_sprite.center_x = 700
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
            fireball.scale = 1.0
            
            # Ajouter à la liste
            self.fireball_list.append(fireball)
            
            # Reset du cooldown
            self.fireball_cooldown_timer = 0

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
        self.fireball_list.draw()

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

        # Système de fireball
        self.fireball_cooldown_timer += delta_time
        if (self.fireball_cooldown_timer >= FIREBALL_COOLDOWN and 
            not self.follower_charging and not self.follower_attacking and 
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
                
                # Vérifier collision avec le boss
                if (abs(fireball.center_x - self.player_sprite.center_x) < 30 and
                    abs(fireball.center_y - self.player_sprite.center_y) < 30):
                    # Collision détectée
                    fireball.start_explosion()
                    self.player_health -= FIREBALL_DAMAGE
                    if self.player_health <= 0:
                        try:
                            self.player_sprite.kill()
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
                    hit_frame = min(1, len(self.attack_textures)-1) if len(self.attack_textures) > 0 else None
                    if hit_frame is not None and self.current_frame == hit_frame and not self.player_dealt_damage:
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