import random
# Configurações e constantes
WIDTH, HEIGHT = 800, 500
TITLE = "O Jogo Mais Difícil do Mundo"
GAME_MENU, GAME_PLAYING, GAME_OVER, GAME_VICTORY = 0, 1, 2, 3

# Áreas do jogo
playable_area = Rect((70, 70), (WIDTH-140, HEIGHT-140))
start_area = Rect((20, HEIGHT/2-50), (50, 100))
finish_area = Rect((WIDTH-70, HEIGHT/2-50), (50, 100))
start_button = Rect((WIDTH/2 - 150, HEIGHT/2 - 60), (300, 50))
music_button = Rect((WIDTH/2 - 150, HEIGHT/2), (300, 50))
exit_button = Rect((WIDTH/2 - 150, HEIGHT/2 + 60), (300, 50))

# Vidas máximas permitidas
DEATHS_MAX = 5

class Entity:
    def __init__(self, x, y, w, h, speed=5):
        self.x, self.y, self.w, self.h, self.speed = x, y, w, h, speed
        self.actor = None  # Imagem do ator, definida nas subclasses
    
    def get_rect(self): 
        return Rect((self.x - self.w/2, self.y - self.h/2), (self.w, self.h))
    
    def update_actor_pos(self):
        # Atualiza a posição do ator para corresponder à entidade
        if self.actor:
            self.actor.pos = (self.x, self.y)

class Player(Entity):
    def __init__(self):
        super().__init__(start_area.x + start_area.width/3, start_area.y + start_area.height/2, 32, 32)
        self.frame, self.frame_count, self.frame_speed = 0, 0, 8
        self.is_moving, self.direction = False, 1
        # Usando imagens da pasta 'images'
        self.actor = Actor('personagem_parado', anchor=('center', 'center'))
    
    def update(self):
        old_x, old_y = self.x, self.y
        self.is_moving = False
        
        # Movimento
        if keyboard.left or keyboard.a: self.x -= self.speed; self.is_moving = True; self.direction = -1
        if keyboard.right or keyboard.d: self.x += self.speed; self.is_moving = True; self.direction = 1
        if keyboard.up or keyboard.w: self.y -= self.speed; self.is_moving = True
        if keyboard.down or keyboard.s: self.y += self.speed; self.is_moving = True
        
        # Verificar limites
        player_rect = self.get_rect()
        in_playable = all([player_rect.left >= playable_area.left, player_rect.right <= playable_area.right,
                          player_rect.top >= playable_area.top, player_rect.bottom <= playable_area.bottom])
        in_start = all([player_rect.left >= start_area.left, player_rect.right <= start_area.right,
                       player_rect.top >= start_area.top, player_rect.bottom <= start_area.bottom])
        in_finish = all([player_rect.left >= finish_area.left, player_rect.right <= finish_area.right,
                        player_rect.top >= finish_area.top, player_rect.bottom <= finish_area.bottom])
        transitioning = (player_rect.colliderect(start_area) and player_rect.colliderect(playable_area)) or \
                        (player_rect.colliderect(finish_area) and player_rect.colliderect(playable_area))
        
        # Reverter se fora dos limites
        if not (in_playable or in_start or in_finish or transitioning):
            self.x, self.y = old_x, old_y; self.is_moving = False
        
        # Garantir dentro da tela e atualizar animação
        self.x, self.y = max(self.w/2, min(WIDTH - self.w/2, self.x)), max(self.h/2, min(HEIGHT - self.h/2, self.y))
        self.frame_count += 1.5 if self.is_moving else 0.5
        if self.frame_count >= self.frame_speed: self.frame = (self.frame + 1) % 4; self.frame_count = 0
    
    def draw(self, screen):
        # Atualiza a imagem do jogador com base no movimento
        self.actor.image = 'personagem_correndo' if self.is_moving else 'personagem_parado'
        self.update_actor_pos()
        self.actor.draw()

class Enemy(Entity):
    def __init__(self, level):
        x, y = random.randint(100, WIDTH-100), random.randint(100, HEIGHT-100)
        super().__init__(x, y, 32, 32, random.choice([-2, 2]) * (0.5 + level * 0.1))
        self.radius = 20
        self.speed_y = random.choice([-2, 2]) * (0.5 + level * 0.1) # velocidade aumenta conforme o nível
        self.direction = 1 if self.speed > 0 else -1
        self.frame_count, self.frame_speed = 0, 10
        self.mouth_open = False
        # Escolhe um tipo de inimigo aleatório (0-3)
        self.inimigo_tipo = random.randint(0, 3)
        # Cria o ator com a imagem inicial
        self.actor = Actor(f'inimigo{self.inimigo_tipo}_fechado', anchor=('center', 'center'))
    
    def update(self):
        old_x, old_y = self.x, self.y
        self.x += self.speed; self.y += self.speed_y
        
        # Limites
        if (self.x - self.radius < playable_area.x) or (self.x + self.radius > playable_area.x + playable_area.width):
            self.speed *= -1; self.x = old_x + self.speed; self.direction = 1 if self.speed > 0 else -1
        if (self.y - self.radius < playable_area.y) or (self.y + self.radius > playable_area.y + playable_area.height):
            self.speed_y *= -1; self.y = old_y + self.speed_y
        
        # Animação
        self.frame_count += 1
        if self.frame_count >= self.frame_speed:
            self.frame_count = 0
            self.mouth_open = not self.mouth_open
            # Alterna entre boca aberta e fechada
            self.actor.image = f'inimigo{self.inimigo_tipo}_' + ('aberto' if self.mouth_open else 'fechado')
    
    def draw(self, screen):
        # Atualiza a posição do ator
        self.update_actor_pos()
        # Desenha o inimigo
        self.actor.draw()

class Game:
    def __init__(self):
        self.state, self.level, self.max_level = GAME_MENU, 1, 30
        self.deaths, self.missions_completed = 0, 0
        self.is_gameover, self.is_victory, self.music_on = False, False, False
        self.level_pause = 0  # Contador para pausa entre níveis
        self.death_pause = 0  # Contador para pausa após morte
        self.player = Player()
        self.enemies = []
        self.initialize_level()
    
    def initialize_level(self):
        # Define os inimigos    
        self.enemies = []
        for i in range(1 + self.level):
            # Posiciona inimigos em locais diferentes para não ficarem agrupados
            enemy = Enemy(self.level)
            if i > 0:  # Varia a posição dos inimigos adicionais
                enemy.x = WIDTH/2 + (i % 3 - 1) * 80
                enemy.y = HEIGHT/2 + (i % 2) * 100 - 50
            self.enemies.append(enemy)
            
        self.player.x, self.player.y = start_area.x + start_area.width/3, start_area.y + start_area.height/2
        self.player.direction, self.player.is_moving = 1, False
        self.player.frame, self.player.frame_count = 0, 0
    
    # Ação executada quando o herói morreu
    def player_died(self):
        self.deaths += 1
        sounds.hurt.play()
        # Ativar a pausa de 1.5 segundos (90 frames em 60fps)
        self.death_pause = 90
        if self.deaths >= DEATHS_MAX: self.is_gameover = True
    
    # Ação executada quando o herói completou o nível
    def level_complete(self):
        sounds.win.play()
        # Ativar a pausa de 2 segundos (120 frames em 60fps)
        self.level_pause = 120
        self.level += 1; self.missions_completed += 1
    
    def update(self):
        if self.state != GAME_PLAYING or self.is_gameover or self.is_victory: return
        
        # Se estiver em pausa entre níveis
        if self.level_pause > 0:
            self.level_pause -= 1
            # Quando terminar a pausa, inicializar o próximo nível
            if self.level_pause == 0:
                for enemy in self.enemies: enemy.speed *= 1.2; enemy.speed_y *= 1.2
                self.player.x, self.player.y = start_area.x + start_area.width/2, start_area.y + start_area.height/2
                if self.level > self.max_level: self.is_victory = True
                self.initialize_level()
            return  # Não atualiza o jogo durante a pausa
            
        # Se estiver em pausa após morte
        if self.death_pause > 0:
            self.death_pause -= 1
            # Quando terminar a pausa, reposicionar o jogador
            if self.death_pause == 0:
                self.player.x, self.player.y = start_area.x + start_area.width/3, start_area.y + start_area.height/2
            return  # Não atualiza o jogo durante a pausa
        
        self.player.update()
        for enemy in self.enemies: enemy.update()
        
        # Colisões
        for enemy in self.enemies:
            if ((self.player.x-enemy.x)**2 + (self.player.y-enemy.y)**2)**0.5 < (self.player.w/2 + enemy.radius):
                self.player_died()
        
        # Verificar chegada
        if self.player.get_rect().colliderect(finish_area): self.level_complete()
    
    def draw(self, screen):
        screen.fill((200, 200, 255))
        
        if self.state == GAME_MENU:
            # Menu
            screen.draw.text("O JOGO MAIS DIFÍCIL DO MUNDO", center=(WIDTH/2, HEIGHT/4), fontsize=40, color=(0, 0, 0))
            for btn, color, text in [(start_button, (150, 255, 150), "COMEÇAR JOGO"), 
                                  (music_button, (150, 200, 255), "DESLIGAR MÚSICA" if self.music_on else "LIGAR MÚSICA"),
                                  (exit_button, (255, 150, 150), "SAIR")]:
                screen.draw.filled_rect(btn, color); screen.draw.rect(btn, (0, 0, 0))
                screen.draw.text(text, center=(WIDTH/2, btn.centery), fontsize=30, color=(0, 0, 0))
        elif self.state == GAME_PLAYING:
            # Jogo
            screen.draw.filled_rect(playable_area, (240, 240, 240))
            screen.draw.filled_rect(start_area, (150, 255, 150))
            screen.draw.filled_rect(finish_area, (150, 255, 150))
            
            self.player.draw(screen)
            for enemy in self.enemies: enemy.draw(screen)
            
            # Interface
            screen.draw.text(f"Vidas: {DEATHS_MAX - self.deaths}", topright=(WIDTH-10, 0), fontsize=30, color=(0, 0, 0))
            screen.draw.text(f"Missões: {self.missions_completed}", center=(WIDTH/2, 10), fontsize=30, color=(0, 0, 0))
            screen.draw.filled_rect(Rect((0, 0), (100, 30)), (0, 0, 0))
            screen.draw.text("MENU", center=(50, 15), fontsize=20, color=(255, 255, 255))
            
            # Mensagens de fim
            if self.is_gameover:
                screen.draw.text("GAME OVER", center=(WIDTH/2, HEIGHT/2), fontsize=60, color=(255, 0, 0))
                screen.draw.text("Pressione ESPAÇO para recomeçar", center=(WIDTH/2, HEIGHT/2+50), fontsize=30, color=(0, 0, 0))
            if self.is_victory:
                screen.draw.text("VITÓRIA!", center=(WIDTH/2, HEIGHT/2), fontsize=60, color=(0, 255, 0))
                screen.draw.text(f"Completou com {self.deaths} mortes!", center=(WIDTH/2, HEIGHT/2+50), fontsize=30, color=(0, 0, 0))
            # Mostrar mensagem de nível completo durante a pausa
            if self.level_pause > 0:
                screen.draw.text("MISSÃO COMPLETA!", center=(WIDTH/2, HEIGHT/2), fontsize=60, color=(0, 200, 0))
                screen.draw.text(f"Próximo nível: {self.level}", center=(WIDTH/2, HEIGHT/2+50), fontsize=30, color=(0, 0, 0))
            
            # Mostrar mensagem de morte durante a pausa
            if self.death_pause > 0 and not self.is_gameover:
                screen.draw.text("VOCÊ MORREU!", center=(WIDTH/2, HEIGHT/2), fontsize=60, color=(255, 0, 0))
                screen.draw.text(f"Vidas: {DEATHS_MAX - self.deaths}", center=(WIDTH/2, HEIGHT/2+50), fontsize=30, color=(0, 0, 0))

# Inicialização e funções Pygame Zero
game = Game()
def draw(): game.draw(screen)
def update(): game.update()

def on_key_down(key):
    if game.state == GAME_PLAYING:
        if (game.is_gameover or game.is_victory) and key == keys.SPACE:
            game.is_gameover, game.is_victory = False, False
            game.level, game.deaths, game.missions_completed = 1, 0, 0
            game.initialize_level()
        if key == keys.ESCAPE: game.state = GAME_MENU

def on_mouse_down(pos):
    if game.state == GAME_MENU:
        if start_button.collidepoint(pos): game.state = GAME_PLAYING; game.initialize_level()
        elif music_button.collidepoint(pos):
            game.music_on = not game.music_on
            if game.music_on: music.play('background'); music.set_volume(0.1)
            else: music.stop()
        elif exit_button.collidepoint(pos): exit()
    elif game.state == GAME_PLAYING and Rect((0, 0), (100, 30)).collidepoint(pos): game.state = GAME_MENU
