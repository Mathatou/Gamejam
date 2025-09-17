"""
Menu with textured buttons (idle/hover/pressed) + pixel text overlay.
Arcade 3.3.2 compatible.
"""

import arcade
import arcade.gui
from main import MainView

# --- chemins des sprites ---
BUTTON_FOLDER = "assets/sprites/Button"
BUTTON_IDLE = f"{BUTTON_FOLDER}/button_idle.png"
BUTTON_HOVER = f"{BUTTON_FOLDER}/button_hover.png"
BUTTON_PRESSED = f"{BUTTON_FOLDER}/button_pressed.png"


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()

        # UI manager
        self.manager = arcade.gui.UIManager()

        # textures bouton
        idle = arcade.load_texture(BUTTON_IDLE)
        hover = arcade.load_texture(BUTTON_HOVER)
        pressed = arcade.load_texture(BUTTON_PRESSED)
        btn_w, btn_h = idle.width, idle.height

        # boutons (Start / Exit)
        self.start_button = arcade.gui.UITextureButton(
            texture=idle, texture_hovered=hover, texture_pressed=pressed,
            width=btn_w, height=btn_h
        )
        self.exit_button = arcade.gui.UITextureButton(
            texture=idle, texture_hovered=hover, texture_pressed=pressed,
            width=btn_w, height=btn_h
        )

        # actions
        @self.start_button.event("on_click")
        def _start(_e):
            game_view = MainView(self.window)
            game_view.setup_scene('scene1')
            self.window.show_view(game_view)

        @self.exit_button.event("on_click")
        def _exit(_e):
            arcade.exit()

        # police “pixel” (fallback inclus dans Arcade)
        # Pour une vraie police pixel, placez un .ttf et décommentez load_font + changez font_name.
        arcade.load_font("assets/fonts/Counting Apples.ttf")
        self.font_name = "Counting Apples"

        # labels superposés
        font_size = 24
        self.start_label = arcade.gui.UILabel(
            text="START", font_size=font_size, font_name=self.font_name,
            bold=True, text_color=arcade.color.WHITE
        )
        self.exit_label = arcade.gui.UILabel(
            text="EXIT", font_size=font_size, font_name=self.font_name,
            bold=True, text_color=arcade.color.WHITE
        )

        # rangée = ancre qui empile bouton + label au centre
        def make_row(button, label):
            row = arcade.gui.UIAnchorLayout(width=btn_w, height=btn_h)
            # bouton centré
            row.add(button, anchor_x="center_x", anchor_y="center_y")
            # label centré mais relevé de 20 px
            row.add(label, anchor_x="center_x", anchor_y="center_y", align_y=5)
            return row

        start_row = make_row(self.start_button, self.start_label)
        exit_row = make_row(self.exit_button, self.exit_label)

        # --- GRID LAYOUT (séparation garantie) ---
        self.grid = arcade.gui.UIGridLayout(
            column_count=1, row_count=3, horizontal_spacing=0, vertical_spacing=45
        )
        # ligne 0 : start
        self.grid.add(start_row, column=0, row=0)
        # ligne 1 : spacer (hauteur fixe)
        spacer = arcade.gui.UIWidget(width=1, height=24)
        self.grid.add(spacer, column=0, row=1)
        # ligne 2 : exit
        self.grid.add(exit_row, column=0, row=2)

        # ancrage au centre
        self.root = self.manager.add(arcade.gui.UIAnchorLayout())
        self.root.add(self.grid, anchor_x="center_x", anchor_y="center_y")

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()
