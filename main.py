import math
from kivy.app import App
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate, Ellipse, Line
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager, Screen, WipeTransition
from kivy.properties import StringProperty, NumericProperty
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
import random

Config.set('graphics', 'resizable', True)
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')
from kivy.core.window import Window  # will mess up config if this line is written above

Clock.max_iteration = 30


class MainMenuScreen(Screen):
    pass


class GameMenuScreen(Screen):
    pass


class NewGameScreen(Screen):
    pass


class LoadGameScreen(Screen):
    pass


class GameScreen(Screen):
    level_canvas = None

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.level_canvas = self.canvas


class GameWonScreen(Screen):
    pass


class GameLostScreen(Screen):
    pass


class HallOfFameScreen(Screen):
    primo = StringProperty("")
    secondo = StringProperty("")
    terzo = StringProperty("")

    def on_pre_enter(self):
        self.load_high_scores()

    def load_high_scores(self):
        try:
            with open('assets/high_scores.txt', 'r') as file:
                self.primo = file.readline().strip()
                self.secondo = file.readline().strip()
                self.terzo = file.readline().strip()
        except FileNotFoundError:
            self.primo = "No high scores available."


class HelpScreen(Screen):
    pass


class EndScreen(Screen):
    pass


def get_level(n):
    file_path = f'assets/level_data/{n}.txt'
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        random_line = random.choice(lines)
        character_list = list(random_line)

        return character_list

    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    except ValueError as e:
        raise e



class Projectile(Widget):
    def __init__(self, pos, angle, velocity, mass=0, **kwargs):
        super().__init__(**kwargs)
        self.pos = pos
        self.angle = angle
        self.velocity = velocity
        self.mass = mass
        self.gravity = mass * 9.81
        self.dx = velocity * math.cos(math.radians(angle))
        self.dy = velocity * math.sin(math.radians(angle))
        self.time = 0

    def move(self):
        self.time += 1 / 60  # Increment time based on the frame rate

        # simulate gravity
        if self.mass > 0:
            self.dy -= self.gravity

        # Update position
        self.x += self.dx
        self.y += self.dy
        self.update_graphics()

        # Check if projectile is off-screen
        if self.y < 0 or self.y > Window.height or self.x < 0 or self.x > Window.width:
            self.remove_projectile()

    def update_graphics(self):
        # This method will be overridden by subclasses
        pass

    def remove_projectile(self):
        # This method will be overridden by subclasses
        pass


class Bullet(Projectile):
    def __init__(self, pos, angle, velocity, mass=0.1, **kwargs):
        super().__init__(pos, angle, velocity, mass, **kwargs)
        self.size = (dp(10), dp(10))
        with self.canvas:
            Color(0.2, 0.2, 0.2, 1)
            self.ellipse = Ellipse(pos=self.pos, size=self.size)

    def update_graphics(self):
        self.ellipse.pos = (self.x, self.y)

    def remove_projectile(self):
        app = App.get_running_app()
        if self.parent:
            self.parent.remove_widget(self)
            if app:
                app.bullets.remove(self)


class Bombshell(Projectile):
    def __init__(self, pos, angle, velocity, mass=0.05, **kwargs):
        super().__init__(pos, angle, velocity * 2.1, mass, **kwargs)
        self.size = (dp(90), dp(90))  # Bombshell is bigger than bullet and laser
        self.texture = CoreImage('assets/weapons/bombshell.png').texture
        with self.canvas:
            Color(1, 1, 1, 1)  # White color to display the texture correctly
            self.rectangle = Rectangle(texture=self.texture, pos=self.pos, size=self.size)

    def update_graphics(self):
        self.rectangle.pos = (self.x, self.y)

    def remove_projectile(self):
        app = App.get_running_app()
        if self.parent:
            self.parent.remove_widget(self)
            if app:
                app.bombshells.remove(self)


class Laser(Projectile):
    def __init__(self, pos, angle, velocity, **kwargs):
        super().__init__(pos, angle, velocity, 0, **kwargs)  # No gravity for laser
        self.size = (dp(20), dp(5))
        with self.canvas:
            Color(1, 0, 0, 1)
            self.line = Line(points=[self.x, self.y, self.x + self.dx, self.y + self.dy], width=dp(2))

    def update_graphics(self):
        self.line.points = [self.x, self.y, self.x + self.dx, self.y + self.dy]

    def remove_projectile(self):
        app = App.get_running_app()
        if self.parent:
            self.parent.remove_widget(self)
            if app:
                app.lasers.remove(self)

    def reflect(self, mirror_orientation):
        if mirror_orientation == 'vertical':
            self.dx = -self.dx
            self.angle = 180 - self.angle
        elif mirror_orientation == 'horizontal':
            self.dy = -self.dy
            self.angle = -self.angle


def reflect_laser(self, laser, collidable):
    mirror_x, mirror_y = collidable['x'], collidable['y']
    mirror_width, mirror_height = collidable['width'], collidable['height']
    laser_centre_x = laser.x + laser.size[0] / 2
    laser_centre_y = laser.y + laser.size[1] / 2

    # Compute distances from the laser to the sides of the mirror
    top_dist = mirror_y + mirror_height - laser_centre_y
    bottom_dist = laser_centre_y - mirror_y
    left_dist = laser_centre_x - mirror_x
    right_dist = mirror_x + mirror_width - laser_centre_x

    # Determine the closest side of the mirror to reflect accurately
    min_dist = min(top_dist, bottom_dist, left_dist, right_dist)
    if min_dist == top_dist or min_dist == bottom_dist:
        laser.reflect('horizontal')
    else:
        laser.reflect('vertical')


class CannonApp(App):
    input_field = None
    current_score = 0
    current_level = 0
    current_username = None
    game_won_called = False
    projectile_types = ['bullet', 'bomb', 'laser']
    current_projectile_index = 0
    muzzle_velocity = 1
    max_shots = NumericProperty(0)
    remaining_shots = NumericProperty(0)

    def __init__(self, **kwargs):
        super(CannonApp, self).__init__(**kwargs)
        self.current_level_data = None
        self.sounds = [
            SoundLoader.load('assets/audio/01.wav'),
            SoundLoader.load('assets/audio/02.wav'),
            SoundLoader.load('assets/audio/03.wav'),
            SoundLoader.load('assets/audio/04.wav')
        ]
        self.bullets = []
        self.bombshells = []
        self.lasers = []
        self.cannon_angle = 0

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='menu'))
        sm.add_widget(GameMenuScreen(name='gamemenu'))
        sm.add_widget(NewGameScreen(name='newgame'))
        sm.add_widget(LoadGameScreen(name='loadgame'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(HallOfFameScreen(name='hof'))
        sm.add_widget(HelpScreen(name='help'))
        sm.add_widget(GameWonScreen(name='gamewon'))
        sm.add_widget(GameLostScreen(name='gamelost'))
        sm.add_widget(EndScreen(name='ending'))
        sm.transition = WipeTransition()

        Window.bind(on_touch_down=self.on_mouse_click)
        Window.bind(mouse_pos=self.on_mouse_move)
        Window.bind(on_key_down=self.on_key_down)
        Window.bind(on_resize=self.on_window_resize)

        Clock.schedule_interval(self.update_projectyles, 1 / 30)  # 30 FPS
        return sm

    def on_window_resize(self, window, width, height):
        self.redraw_level()

    def redraw_level(self):
        game_screen = self.root.get_screen('game')
        # Clear only level tiles and not UI
        game_screen.ids.level_canvas.canvas.clear()
        self.draw_level(self.current_level_data, True)

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        if key == 32:  # Space bar
            self.cycle_projectile()
        elif key == 97:  # A key
            self.decrease_velocity()
        elif key == 100:  # D key
            self.increase_velocity()

    def cycle_projectile(self):
        self.current_projectile_index = (self.current_projectile_index + 1) % len(self.projectile_types)
        projectile = self.projectile_types[self.current_projectile_index]
        self.root.get_screen('game').ids.projectile_label.text = projectile

    def decrease_velocity(self):
        if self.muzzle_velocity > 1:
            self.muzzle_velocity -= 1
            self.update_velocity_display()

    def increase_velocity(self):
        if self.muzzle_velocity < 5:
            self.muzzle_velocity += 1
            self.update_velocity_display()
            print(self.muzzle_velocity)

    def update_velocity_display(self):
        game_screen = self.root.get_screen('game')
        game_screen.ids.velocity_button.background_disabled_normal = f'assets/velocity/{self.muzzle_velocity}.png'

    def on_mouse_click(self, instance, touch):
        if touch.button == 'left' and self.sounds:
            sound_to_play = random.choice(self.sounds)
            sound_to_play.play()
            if self.root.current == 'game':
                self.fire_projectyle()

    def on_mouse_move(self, window, pos):
        fixed_point = (0, Window.height / 2)
        mouse_x, mouse_y = pos
        angle_radians = math.atan2(mouse_y - fixed_point[1], mouse_x - fixed_point[0])
        self.cannon_angle = math.degrees(angle_radians)
        self.root.get_screen('game').ids.scatter.rotation = self.cannon_angle
        print(pos, self.cannon_angle)

    def fire_projectyle(self):
        if self.remaining_shots > 0:
            if self.current_projectile_index == 0:
                self.fire_bullet()
            elif self.current_projectile_index == 1:
                self.fire_bombshell()
            elif self.current_projectile_index == 2:
                self.fire_laser()

            # Decrease remaining shots and update label
            self.remaining_shots -= 1
            self.root.get_screen('game').ids.shots_label.text = f"Shots: {self.remaining_shots}/{self.max_shots}"
        else:
            self.root.current = 'gamelost'

    def fire_bullet(self):
        cannon_pos = (0, Window.height / 2)  # Starting position of the cannon
        bullet_velocity = 20 * self.muzzle_velocity  # Calculate velocity based on the current muzzle_velocity
        bullet = Bullet(pos=cannon_pos, angle=self.cannon_angle, velocity=bullet_velocity)
        game_screen = self.root.get_screen('game')
        scatter_index = game_screen.children.index(game_screen.ids.scatter)
        game_screen.add_widget(bullet, index=scatter_index + 1)
        self.bullets.append(bullet)

    def fire_bombshell(self):
        cannon_pos = (0, Window.height / 2)
        bombshell_velocity = 10 * self.muzzle_velocity
        bombshell = Bombshell(pos=cannon_pos, angle=self.cannon_angle, velocity=bombshell_velocity)
        game_screen = self.root.get_screen('game')
        scatter_index = game_screen.children.index(game_screen.ids.scatter)
        game_screen.add_widget(bombshell, index=scatter_index + 1)
        self.bombshells.append(bombshell)

    def fire_laser(self):
        cannon_pos = (0, Window.height / 2)
        laser_velocity = 50
        laser = Laser(pos=cannon_pos, angle=self.cannon_angle, velocity=laser_velocity)
        game_screen = self.root.get_screen('game')
        scatter_index = game_screen.children.index(game_screen.ids.scatter)
        game_screen.add_widget(laser, index=scatter_index + 1)
        self.lasers.append(laser)

    def update_projectyles(self, dt):
        # Combine all projectiles into a single list
        all_projectiles = self.bullets + self.bombshells + self.lasers

        for p in all_projectiles:
            p.move()
            self.check_collisions(p)

    def check_collisions(self, projectile):
        for collidable in self.collidables:
            if self.is_colliding(projectile, collidable):
                self.handle_collision(projectile, collidable)

    def is_colliding(self, projectile, collidable):
        px, py = projectile.x, projectile.y
        if projectile in self.bullets:
            pw, ph = 10, 10
        elif projectile in self.bombshells:
            pw, ph = 90, 90
        elif projectile in self.lasers:
            pw, ph = 5, 5
        else:
            pw, ph = 0, 0

        cx, cy = collidable['x'], collidable['y']
        cw, ch = collidable['width'], collidable['height']

        # collision detection
        if (px < cx + cw and
                px + pw > cx and
                py < cy + ch and
                py + ph > cy):
            return True

    def handle_collision(self, projectile, collidable):
        if collidable.get('type') == 't':
            if not self.game_won_called:
                self.game_won()
                self.game_won_called = True
            return
        if isinstance(projectile, Bullet):
            if collidable.get('type') == 'r':
                self.current_level_data[collidable.get('coord')] = 'n'
                self.redraw_level()
            projectile.remove_projectile()
        elif isinstance(projectile, Bombshell):
            if collidable.get('type') == 'r':
                self.current_level_data[collidable.get('coord')] = 'n'
                self.redraw_level()
            self.bomb_explosion_collisions(projectile)
            projectile.remove_projectile()
        elif isinstance(projectile, Laser):
            if collidable.get('type') == 'm':
                self.reflect_laser(projectile, collidable)
            else:
                projectile.remove_projectile()

    def reflect_laser(self, laser, collidable):
        mirror_x, mirror_y = collidable['x'], collidable['y']
        mirror_width, mirror_height = collidable['width'], collidable['height']
        laser_centre_x = laser.x + 2.5
        laser_centre_y = laser.y + 2.5
        top = mirror_y + mirror_height - laser_centre_y
        bottom = laser_centre_y - mirror_y
        left = laser_centre_x - mirror_x
        right = mirror_x + mirror_width - laser_centre_x
        # calculates which side of the mirror is hit
        if top < left and right or bottom < left and right:
            laser.reflect('horizontal')
        else:
            laser.reflect('vertical')

    def bomb_explosion_collisions(self, projectile):
        for collidable in self.collidables:
            if self.is_exploding(projectile, collidable):
                self.handle_explosion(collidable)

    def is_exploding(self, projectile, collidable):  # collision detection for bomb explosion radius
        radius = ((0.75 * Window.width) / 8 + Window.height / 6) / 2
        px, py = projectile.x - radius + 90, projectile.y - radius + 90
        pw, ph = 2 * radius, 2 * radius

        cx, cy = collidable['x'], collidable['y']
        cw, ch = collidable['width'], collidable['height']

        if (px < cx + cw and
                px + pw > cx and
                py < cy + ch and
                py + ph > cy):
            return True

    def handle_explosion(self, collidable):
        if collidable.get('type') == 'r':
            self.current_level_data[collidable.get('coord')] = 'n'
            self.redraw_level()

    def game_won(self):
        self.current_level += 1
        if self.current_level == 4:
            self.the_end()
            return
        self.current_score = self.current_score + ((self.remaining_shots * 10) + 10) * 10 * self.current_level
        self.root.get_screen('gamewon').ids.score_label.text = f'You won! Score: {self.current_score}'
        self.root.current = 'gamewon'

    def continue_playing(self):
        self.init_game(self.current_username, self.current_level, self.current_score)

    def save_and_quit(self):
        new_profile_line = f"{self.current_username}%{self.current_level}%{self.current_score}\n"

        # Read the existing profiles
        try:
            with open('assets/profiles.txt', 'r') as file:
                lines = file.readlines()
        except FileNotFoundError:
            lines = []

        # Remove the existing profile for the same username if it exists
        lines = [line for line in lines if not line.startswith(f"{self.current_username}%")]

        # Insert the new profile line
        lines.insert(0, new_profile_line)

        # Write the updated profile list back to the file
        with open('assets/profiles.txt', 'w') as file:
            file.writelines(lines)

        self.switch_to_menu()

    def the_end(self):
        self.root.get_screen('ending').ids.end_label.text = f'You won the game! Final score: {self.current_score}'
        self.update_hof(self.current_username, self.current_score)
        self.root.current = 'ending'

    def update_hof(self, username, score):
        hof_file = 'assets/high_scores.txt'

        try:
            with open(hof_file, 'r') as file:
                lines = file.readlines()
        except FileNotFoundError:
            lines = []

        # put existing scores into a list of tuples (score, username)
        scores = []
        for line in lines:
            line = line.strip()
            if line:
                name, score_str = line.rsplit(': ', 1)
                try:
                    score_value = int(score_str)
                    scores.append((score_value, name))
                except ValueError:
                    continue

        # Add the new score to the list
        scores.append((score, username))

        # Sort the scores highest score first
        scores.sort(reverse=True, key=lambda x: x[0])

        # Keep only the top 3 scores
        top_scores = scores[:3]

        # Write the top 3 scores back to the file
        with open(hof_file, 'w') as file:
            for score, name in top_scores:
                file.write(f'{name}: {score}\n')

    def switch_to_gamemenu(self):
        self.root.current = 'gamemenu'

    def switch_to_game(self):
        self.root.current = 'game'

    def switch_to_hof(self):
        self.root.current = 'hof'

    def switch_to_help(self):
        self.root.current = 'help'

    def switch_to_menu(self):
        self.root.current = 'menu'

    def new_game(self):
        self.root.current = 'newgame'

    def load_game(self):
        self.root.current = 'loadgame'
        self.load_profiles()

    def load_profiles(self):
        load_screen = self.root.get_screen('loadgame')

        # Clear existing widgets in load_screen
        load_screen.clear_widgets()

        # Create ScrollView
        scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)

        # Create a BoxLayout for vertical orientation
        main_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))

        spacer = Widget(size_hint_y=None, height=80)

        # Create GridLayout
        layout = GridLayout(cols=1, spacing=100, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        try:
            with open('assets/profiles.txt', 'r') as file:
                lines = file.readlines()

            for line in lines:
                name, levels_completed, score = line.strip().split('%')
                load_button = Button(
                    text=f'Load {name}: {levels_completed} Levels Completed, Score: {score}',
                    size_hint_y=None,
                    height=50,
                    font_size=0.03 * self.root.width,
                    font_name='assets/SuperMario256.ttf',
                    background_normal='assets/X_bg_up.png',
                    background_color=[1, 1, 1, 1],
                    on_release=lambda btn, n=name, l=int(levels_completed), s=int(score): self.init_game(n, l, s)
                )
                layout.add_widget(load_button)

        except FileNotFoundError:
            error_label = Label(text="No profiles found.", font_size='20sp')
            layout.add_widget(error_label)

        # Add the spacer and GridLayout to the BoxLayout
        main_layout.add_widget(spacer)
        main_layout.add_widget(layout)

        # Add the BoxLayout to the ScrollView
        scroll_view.add_widget(main_layout)

        # Add ScrollView to the screen
        load_screen.add_widget(scroll_view)

    def init_new_game(self):
        profile_name = self.root.get_screen('newgame').ids.input.text
        if profile_name != "":
            profile_name = profile_name.strip()
            return self.init_game(profile_name, 0, 0)
        else:
            return self.new_game()

    def init_game(self, username, lvl, score):
        self.game_won_called = False
        self.root.current = 'game'
        self.current_score = score
        self.current_level = lvl
        self.current_username = username
        self.level(lvl)

    def draw_level(self, leveldata, redrawing=False):
        self.current_level_data = leveldata
        self.collidables = []
        t_found = False

        # Get the current window size and calculate scale factors
        window_width, window_height = Window.size
        base_width, base_height = 1920, 1080
        scale_x = window_width / base_width
        scale_y = window_height / base_height

        # Set tile size based on scaling factors
        tile_width = 180 * scale_x
        tile_height = 180 * scale_y
        base_x_pos = 480 * scale_x
        base_y_pos = 0 * scale_y

        # Texture mappings
        textures = {
            'r': 'assets/tiles/rock.png',
            'm': 'assets/tiles/mirror.png',
            't': 'assets/tiles/target.png',
            'p': 'assets/tiles/perpetio.png',
            'g': 'assets/tiles/gravitonio.png',
            '1': 'assets/tiles/wormhole_orange.png',
            '2': 'assets/tiles/wormhole_orange.png',
            '3': 'assets/tiles/wormhole_orange.png',
            '4': 'assets/tiles/wormhole_orange.png',
            '5': 'assets/tiles/wormhole_blue.png',
            '6': 'assets/tiles/wormhole_blue.png',
            '7': 'assets/tiles/wormhole_blue.png',
            '8': 'assets/tiles/wormhole_blue.png'

        }

        # Access level drawing canvas
        game_screen = self.root.get_screen('game')
        level_canvas = game_screen.ids.level_canvas.canvas
        level_canvas.clear()

        # iterating through level data to draw each tile
        for i in range(48):
            x_pos = base_x_pos + ((i % 8) * tile_width)
            y_pos = base_y_pos + ((i // 8) * tile_height)

            element = leveldata[i]

            if element == 'n':
                continue

            if element == 't':
                if t_found:
                    element = 'n'
                else:
                    t_found = True

            if element in textures:
                level_canvas.add(Color(1, 1, 1, 1))  # Set the color
                texture = CoreImage(textures[element]).texture
                level_canvas.add(Rectangle(texture=texture, pos=(x_pos, y_pos), size=(tile_width, tile_height)))

                if element in 'rtmp':  # the collidables: rock, target, mirror, perpetio
                    self.collidables.append({
                        'type': element,
                        'x': x_pos,
                        'y': y_pos,
                        'width': tile_width,
                        'height': tile_height,
                        'coord': i
                    })

        if leveldata and not redrawing:  # makes sure remaining shots are not reset when redrawing a level
            max_shots_char = leveldata[48]
            if max_shots_char.isdigit():
                self.max_shots = int(max_shots_char)
                self.remaining_shots = self.max_shots
                self.root.get_screen('game').ids.shots_label.text = f"Shots: {self.remaining_shots}/{self.max_shots}"

    def level(self, n):
        leveldata = get_level(n + 1)
        self.draw_level(leveldata)


if __name__ == '__main__':
    CannonApp().run()
