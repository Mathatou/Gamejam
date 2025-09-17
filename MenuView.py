"""
Menu with textured buttons (idle/hover/pressed) + pixel text overlay.
Arcade 3.3.2 compatible.
"""

import arcade
import arcade.gui
from main import MainView

# --- chemins des sprites ---
BUTTON_FOLDER = "assets/sprites/Button"
START_IDLE = f"{BUTTON_FOLDER}/start_idle.png"
START_HOVER = f"{BUTTON_FOLDER}/start_hover.png"
START_PRESSED = f"{BUTTON_FOLDER}/start_pressed.png"
EXIT_IDLE = f"{BUTTON_FOLDER}/exit_idle.png"
EXIT_HOVER = f"{BUTTON_FOLDER}/exit_hover.png"
EXIT_PRESSED = f"{BUTTON_FOLDER}/exit_pressed.png"


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()

        # UI manager
        self.manager = arcade.gui.UIManager()

        # textures bouton
        start_idle = arcade.load_texture(START_IDLE)
        start_hover = arcade.load_texture(START_HOVER)
        start_pressed = arcade.load_texture(START_PRESSED)
        exit_idle = arcade.load_texture(EXIT_IDLE)
        exit_hover = arcade.load_texture(EXIT_HOVER)
        exit_pressed = arcade.load_texture(EXIT_PRESSED)
        btn_w, btn_h = start_idle.width, start_idle.height

        # boutons (Start / Exit)
        self.start_button = arcade.gui.UITextureButton(
            texture=start_idle, texture_hovered=start_hover, texture_pressed=start_pressed,
            width=btn_w, height=btn_h
        )
        self.exit_button = arcade.gui.UITextureButton(
            texture=exit_idle, texture_hovered=exit_hover, texture_pressed=exit_pressed,
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

        # rangée = ancre qui empile bouton + label au centre
        def make_row(button):
            row = arcade.gui.UIAnchorLayout(width=btn_w, height=btn_h)
            # bouton centré
            row.add(button, anchor_x="center_x", anchor_y="center_y")
            return row

        start_row = make_row(self.start_button)
        exit_row = make_row(self.exit_button)

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
