"""
Menu with textured buttons (idle/hover/pressed) + pixel text overlay.
Arcade 3.3.2 compatible.
"""
import random

import arcade
import arcade.gui

# --- chemins des sprites ---
BUTTON_FOLDER = "assets/sprites/Button"
START_IDLE = f"{BUTTON_FOLDER}/start_idle.png"
START_HOVER = f"{BUTTON_FOLDER}/start_hover.png"
START_PRESSED = f"{BUTTON_FOLDER}/start_pressed.png"
EXIT_IDLE = f"{BUTTON_FOLDER}/exit_idle.png"
EXIT_HOVER = f"{BUTTON_FOLDER}/exit_hover.png"
EXIT_PRESSED = f"{BUTTON_FOLDER}/exit_pressed.png"
OPTIONS_IDLE = f"{BUTTON_FOLDER}/options_idle.png"
OPTIONS_HOVER = f"{BUTTON_FOLDER}/options_hover.png"
OPTIONS_PRESSED = f"{BUTTON_FOLDER}/options_pressed.png"
BACK_IDLE = f"{BUTTON_FOLDER}/back_idle.png"
BACK_HOVER = f"{BUTTON_FOLDER}/back_hover.png"
BACK_PRESSED = f"{BUTTON_FOLDER}/back_pressed.png"
OPTIONS_BACKGROUND = f"{BUTTON_FOLDER}/options_bg.png"


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()

        # UI manager
        self.manager = arcade.gui.UIManager()

        self.backgrounds = []
        self.backgrounds.append(arcade.load_texture("assets/backgrounds/bg_1.png"))
        self.backgrounds.append(arcade.load_texture("assets/backgrounds/bg_2.png"))

        self.rnd_bg_index = random.randint(0, len(self.backgrounds)-1)

        # textures bouton
        start_idle = arcade.load_texture(START_IDLE)
        start_hover = arcade.load_texture(START_HOVER)
        start_pressed = arcade.load_texture(START_PRESSED)
        exit_idle = arcade.load_texture(EXIT_IDLE)
        exit_hover = arcade.load_texture(EXIT_HOVER)
        exit_pressed = arcade.load_texture(EXIT_PRESSED)
        options_idle = arcade.load_texture(OPTIONS_IDLE)
        options_hover = arcade.load_texture(OPTIONS_HOVER)
        options_pressed = arcade.load_texture(OPTIONS_PRESSED)
        btn_w, btn_h = start_idle.width*0.7, start_idle.height*0.7

        # boutons (Start / Exit)
        self.start_button = arcade.gui.UITextureButton(
            texture=start_idle, texture_hovered=start_hover, texture_pressed=start_pressed,
            width=btn_w, height=btn_h
        )
        self.exit_button = arcade.gui.UITextureButton(
            texture=exit_idle, texture_hovered=exit_hover, texture_pressed=exit_pressed,
            width=btn_w, height=btn_h
        )
        self.options_button = arcade.gui.UITextureButton(
            texture=options_idle, texture_hovered=options_hover, texture_pressed=options_pressed,
            width=btn_w, height=btn_h
        )

        # actions
        @self.start_button.event("on_click")
        def _start(_e):
            from main import MainView as _MainView
            game_view = _MainView(self.window)
            game_view.setup_scene('scene1')
            game_view.start_Timer()
            self.window.show_view(game_view)

        @self.exit_button.event("on_click")
        def _exit(_e):
            arcade.exit()

        @self.options_button.event("on_click")
        def on_click_options_button(event):
            options_menu = SubMenu(btn_w, btn_h)
            self.manager.add(options_menu, layer=1)

        # --- GRID LAYOUT (séparation garantie) ---
        self.grid = arcade.gui.UIGridLayout(
            column_count=1, row_count=5, horizontal_spacing=0, vertical_spacing=5
        )
        # ligne 0 : start
        self.grid.add(self.start_button, column=0, row=0)
        # ligne 2 : options
        self.grid.add(self.options_button, column=0, row=2)
        # ligne 4 : exit
        self.grid.add(self.exit_button, column=0, row=4)

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
        arcade.draw_texture_rect(
            self.backgrounds[self.rnd_bg_index],
            arcade.LBWH(0, 0, self.window.width, self.window.height),
        )
        self.manager.draw()

class SubMenu(arcade.gui.UIMouseFilterMixin, arcade.gui.UIAnchorLayout):
    """Acts like a fake view/window."""

    def __init__(
        self, btn_w, btn_h,
    ):
        super().__init__(size_hint=(1, 1))

        back_idle = arcade.load_texture(BACK_IDLE)
        back_hover = arcade.load_texture(BACK_HOVER)
        back_pressed = arcade.load_texture(BACK_PRESSED)
        options_bg = arcade.load_texture(OPTIONS_BACKGROUND)

        # Setup frame which will act like the window.
        frame = self.add(arcade.gui.UIAnchorLayout(width=300, height=400, size_hint=None))
        frame.with_padding(all=20, top=200)

        # Add a background to the window.
        # Nine patch smoothes the edges.
        frame.with_background(texture=options_bg)

        back_button = arcade.gui.UITextureButton(
            texture=back_idle, texture_hovered=back_hover, texture_pressed=back_pressed,
            width=btn_w, height=btn_h
        )
        # The type of event listener we used earlier for the button will not work here.
        back_button.on_click = self.on_click_back_button

        widget_layout = arcade.gui.UIBoxLayout(align="left", space_between=10)

        widget_layout.add(back_button)

        frame.add(child=widget_layout, anchor_x="center_x", anchor_y="top")

    def on_click_back_button(self, event):
        # Removes the widget from the manager.
        # After this the manager will respond to its events like it previously did.
        self.parent.remove(self)