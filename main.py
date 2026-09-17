"""PuzzleMaster - proyecto.py version APK (sin tkinter).
Replica fiel del juego original pero en Kivy para PC y Android.
Original tkinter (140-2000 piezas, winsound, MCI) no corre en Android,
por eso: mismo menu, mismas dificultades, mismos sonidos, tactil.

PC: pip install kivy pillow && python proyecto.py
APK Colab: subir proyecto2-APK-Colab.zip y buildozer android debug
"""
import os
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.image import Image as CoreImage
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "imagenes")

# Mismas dificultades del juego original.
DIFICULTADES = [
    ("140 piezas", 10, 14, 1),
    ("280 piezas", 14, 20, 2),
    ("420 piezas", 20, 21, 3),
    ("630 piezas", 21, 30, 4),
    ("1200 piezas", 30, 40, 5),
    ("2000 piezas", 40, 50, 6),
]
# En celular se avisa: 630+ solo para tablet potente.
AVISO_MOVIL = "En celular usa 140-420. 630+ solo tablet."


def listar_imagenes():
    exts = (".png", ".jpg", ".jpeg")
    rutas = []
    for carpeta in (IMG_DIR, BASE_DIR):
        if os.path.isdir(carpeta):
            for f in sorted(os.listdir(carpeta)):
                if f.lower().endswith(exts):
                    if f.lower().startswith("puzzle_icon"):
                        continue
                    r = os.path.join(carpeta, f)
                    if os.path.isfile(r) and r not in rutas:
                        rutas.append(r)
    return rutas


class GestorSonido:
    def __init__(self):
        self.clic = self._load("sonido_clic.wav")
        self.encaje = self._load("sonido_encaje.wav")
        self.ganar = self._load("sonido_ganar.wav")
        self.voz_bienvenida = self._load("voz_bienvenida.wav")
        self.voz_elige = self._load("voz_elige.wav")
        self.voz_ganaste = self._load("voz_ganaste.wav")
        self.musica_menu = self._load("musica_menu_0.wav")
        self.musica_juego = self._load("musica_juego_0.wav")
        for m in (self.musica_menu, self.musica_juego):
            if m:
                try:
                    m.loop = True
                except Exception:
                    pass

    def _load(self, nombre):
        ruta = os.path.join(BASE_DIR, nombre)
        if not os.path.isfile(ruta):
            return None
        try:
            return SoundLoader.load(ruta)
        except Exception:
            return None

    @staticmethod
    def play(snd, vol=1.0):
        if snd:
            try:
                snd.volume = vol
                snd.play()
            except Exception:
                pass

    def stop_musicas(self):
        for m in (self.musica_menu, self.musica_juego):
            if m:
                try:
                    m.stop()
                except Exception:
                    pass

    def musica(self, cual):
        self.stop_musicas()
        self.play(self.musica_menu if cual == "menu" else self.musica_juego, 0.5)


SONIDOS = GestorSonido()


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.imagen = None
        self.dif_idx = 0
        self.botones_dif = []
        self._build()

    def _build(self):
        raiz = BoxLayout(orientation="vertical", padding=10, spacing=8)
        raiz.add_widget(Label(text="[b][color=ffd700]  PUZZLE MASTER[/color][/b]",
                              markup=True, font_size="26sp",
                              size_hint_y=None, height=48))
        raiz.add_widget(Label(text="Rompecabezas Jigsaw - toca imagen, dificultad y JUGAR",
                              size_hint_y=None, height=28))
        raiz.add_widget(Label(text=AVISO_MOVIL, font_size="12sp",
                              size_hint_y=None, height=24))

        scroll = ScrollView(size_hint=(1, 0.5))
        self.rejilla = GridLayout(cols=3, spacing=8, padding=8,
                                  size_hint_y=None)
        self.rejilla.bind(minimum_height=self.rejilla.setter("height"))
        scroll.add_widget(self.rejilla)
        raiz.add_widget(scroll)

        self.lbl_sel = Label(text="Imagen: (ninguna)",
                             size_hint_y=None, height=30)
        raiz.add_widget(self.lbl_sel)

        raiz.add_widget(Label(text="DIFICULTAD:", size_hint_y=None, height=26))
        fila = GridLayout(cols=3, spacing=8, size_hint_y=None, height=110)
        for i, (texto, f, c, e) in enumerate(DIFICULTADES):
            b = Button(text=f"{'*'*e}\n{texto}\n{f}x{c}",
                       font_size="12sp")
            b.bind(on_press=self._dif_factory(i))
            self.botones_dif.append(b)
            fila.add_widget(b)
        raiz.add_widget(fila)

        barra = BoxLayout(size_hint_y=None, height=60, spacing=8)
        self.btn_mus = Button(text="Musica: On")
        self.btn_mus.bind(on_press=self._toggle_mus)
        barra.add_widget(self.btn_mus)
        jugar = Button(text="JUGAR", background_color=(0.25, 0.73, 0.35, 1),
                       font_size="20sp")
        jugar.bind(on_press=self._jugar)
        barra.add_widget(jugar)
        raiz.add_widget(barra)
        self.add_widget(raiz)
        self.refrescar()
        self._marcar(0)

    def on_enter(self, *a):
        SONIDOS.musica("menu")
        SONIDOS.play(SONIDOS.voz_bienvenida)
        self.refrescar()

    def refrescar(self):
        self.rejilla.clear_widgets()
        imgs = listar_imagenes()
        if not imgs:
            self.rejilla.add_widget(Label(text="Pon imagenes en carpeta 'imagenes'"))
            return
        if self.imagen not in imgs:
            self.imagen = imgs[0]
            self.lbl_sel.text = "Imagen: " + os.path.basename(self.imagen)
        for ruta in imgs:
            b = Button(size_hint_y=None, height=150)
            caja = BoxLayout(orientation="vertical")
            caja.add_widget(Image(source=ruta, fit_mode="contain"))
            caja.add_widget(Label(text=os.path.basename(ruta),
                                  font_size="11sp", size_hint_y=None, height=22))
            b.add_widget(caja)
            b.bind(on_press=self._img_factory(ruta))
            self.rejilla.add_widget(b)

    def _img_factory(self, ruta):
        def cb(_b):
            SONIDOS.play(SONIDOS.clic)
            self.imagen = ruta
            self.lbl_sel.text = "Imagen: " + os.path.basename(ruta)
        return cb

    def _dif_factory(self, idx):
        def cb(_b):
            SONIDOS.play(SONIDOS.clic)
            self.dif_idx = idx
            self._marcar(idx)
        return cb

    def _marcar(self, idx):
        for i, b in enumerate(self.botones_dif):
            b.background_color = (0.3, 0.8, 0.4, 1) if i == idx else (1, 1, 1, 1)

    def _toggle_mus(self, _b):
        if SONIDOS.musica_menu and SONIDOS.musica_menu.state == "play":
            SONIDOS.stop_musicas()
            self.btn_mus.text = "Musica: Off"
        else:
            SONIDOS.musica("menu")
            self.btn_mus.text = "Musica: On"

    def _jugar(self, _b):
        SONIDOS.play(SONIDOS.clic)
        if not self.imagen:
            SONIDOS.play(SONIDOS.voz_elige)
            Popup(title="Aviso", size_hint=(0.7, 0.3),
                  content=Label(text="Elige una imagen primero")).open()
            return
        nombre, rows, cols, _e = DIFICULTADES[self.dif_idx]
        nivel = listar_imagenes().index(self.imagen) + 1
        juego = self.manager.get_screen("juego")
        juego.iniciar(self.imagen, nivel, nombre, rows, cols)
        self.manager.current = "juego"


class PiezaScatter(Scatter):
    def __init__(self, fila, col, objetivo, tol, al_encajar, **kw):
        super().__init__(**kw)
        self.do_rotation = False
        self.do_scale = False
        self.fila = fila
        self.col = col
        self.objetivo = objetivo
        self.tol = tol
        self.al_encajar = al_encajar
        self.colocada = False

    def on_touch_up(self, touch):
        if self.colocada or not self.collide_point(*touch.pos):
            return super().on_touch_up(touch)
        res = super().on_touch_up(touch)
        ox, oy = self.objetivo
        if ((self.pos[0]-ox)**2 + (self.pos[1]-oy)**2) ** 0.5 <= self.tol:
            self.pos = (ox, oy)
            self.colocada = True
            self.do_translation = False
            if self.al_encajar:
                self.al_encajar(self)
        return res


class GameScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.seg = 0
        self.coloc = 0
        self.total = 0
        self.ev = None
        self.preview_on = False
        self.borde_on = False
        self.iman_on = False
        self._build()

    def _build(self):
        raiz = BoxLayout(orientation="vertical", padding=8, spacing=6)
        barra = BoxLayout(size_hint_y=None, height=52, spacing=6)
        bv = Button(text="< Menu", size_hint_x=0.22)
        bv.bind(on_press=self._volver)
        barra.add_widget(bv)
        self.lbl_info = Label(text="Nivel", size_hint_x=0.38, font_size="13sp")
        barra.add_widget(self.lbl_info)
        self.lbl_cuenta = Label(text="0/0", size_hint_x=0.2)
        barra.add_widget(self.lbl_cuenta)
        self.lbl_t = Label(text="00:00", size_hint_x=0.2)
        barra.add_widget(self.lbl_t)
        raiz.add_widget(barra)

        btns = GridLayout(cols=4, spacing=6, size_hint_y=None, height=100)
        self.b_prev = Button(text="Vista previa", font_size="12sp")
        self.b_prev.bind(on_press=lambda *_: self._toggle("prev"))
        self.b_borde = Button(text="Borde", font_size="12sp")
        self.b_borde.bind(on_press=lambda *_: self._toggle("borde"))
        self.b_iman = Button(text="Iman", font_size="12sp")
        self.b_iman.bind(on_press=lambda *_: self._toggle("iman"))
        b_mez = Button(text="Mezclar", font_size="12sp")
        b_mez.bind(on_press=lambda *_: self._armar())
        btns.add_widget(self.b_prev)
        btns.add_widget(self.b_borde)
        btns.add_widget(self.b_iman)
        btns.add_widget(b_mez)
        raiz.add_widget(btns)

        raiz.add_widget(Label(text="Arrastra con el dedo y suelta cerca de su lugar",
                              size_hint_y=None, height=24, font_size="12sp"))
        self.tablero = RelativeLayout()
        raiz.add_widget(self.tablero)
        self.add_widget(raiz)

    def iniciar(self, ruta, nivel, nombre_dif, rows, cols):
        self.ruta = ruta
        self.nivel = nivel
        self.nombre_dif = nombre_dif
        self.rows, self.cols = rows, cols
        self.total = rows * cols
        SONIDOS.musica("juego")
        Clock.schedule_once(lambda _d: self._armar(), 0)

    def _volver(self, *_):
        SONIDOS.play(SONIDOS.clic)
        if self.ev:
            self.ev.cancel()
            self.ev = None
        SONIDOS.musica("menu")
        self.manager.current = "menu"

    def _toggle(self, cual):
        SONIDOS.play(SONIDOS.clic)
        if cual == "prev":
            self.preview_on = not self.preview_on
        elif cual == "borde":
            self.borde_on = not self.borde_on
            self._pintar_borde()
        else:
            self.iman_on = not self.iman_on
            mult = 2.0 if self.iman_on else 1.0
            for sc in self.piezas:
                sc.tol = sc.tol_base * mult
        self._armar(solo_vista=True)

    def _es_borde(self, f, c):
        return f == 0 or f == self.rows-1 or c == 0 or c == self.cols-1

    def _pintar_borde(self):
        for sc in getattr(self, "piezas", []):
            if sc.colocada:
                continue
            try:
                img = sc.children[0]
                if self.borde_on and self._es_borde(sc.fila, sc.col):
                    img.color = (0.6, 1, 0.6, 1)
                else:
                    img.color = (1, 1, 1, 1)
            except Exception:
                pass

    def _armar(self, solo_vista=False):
        if not hasattr(self, "ruta"):
            return
        if not solo_vista:
            self.tablero.clear_widgets()
            self.seg = 0
            self.coloc = 0
            self.lbl_t.text = "00:00"
            if self.ev:
                self.ev.cancel()
            self.ev = Clock.schedule_interval(self._tick, 1.0)
            try:
                nucleo = CoreImage(self.ruta)
            except Exception as e:
                Popup(title="Error", size_hint=(0.8, 0.4),
                      content=Label(text=str(e))).open()
                return
            tex = nucleo.texture
            tw, th = float(tex.width), float(tex.height)
            bw, bh = float(self.tablero.width), float(self.tablero.height)
            if bw < 10 or bh < 10:
                bw, bh = (800.0, 500.0)
            # tablero cuadrado arriba, resto para mezclar
            lado = min(bw, bh * 0.72)
            self.ox, self.oy = (bw-lado)/2, bh-lado-8
            cw, ch = lado / self.cols, lado / self.rows
            self.piezas = []
            for f in range(self.rows):
                for c in range(self.cols):
                    rx = int(c * tw / self.cols)
                    ry = int(th - (f+1) * th / self.rows)
                    region = tex.get_region(rx, ry,
                                            int(tw/self.cols),
                                            int(th/self.rows))
                    img = Image(texture=region, fit_mode="fill",
                                size=(cw, ch), size_hint=(None, None))
                    tol = min(cw, ch) * 0.35
                    sc = PiezaScatter(f, c, (self.ox + c*cw, self.oy + (self.rows-1-f)*ch),
                                      tol, self._encajo,
                                      size=(cw, ch), size_hint=(None, None))
                    sc.tol_base = tol
                    if self.iman_on:
                        sc.tol *= 2.0
                    sc.add_widget(img)
                    self.piezas.append(sc)
            random.shuffle(self.piezas)
            for sc in self.piezas:
                sc.pos = (random.uniform(0, max(1, bw-cw)),
                          random.uniform(0, max(1, (bh-lado)-ch)))
                self.tablero.add_widget(sc)
            self._pintar_borde()
        # vista previa
        for w in list(self.tablero.children):
            if getattr(w, "es_preview", False):
                self.tablero.remove_widget(w)
        if self.preview_on:
            pv = Image(source=self.ruta, fit_mode="contain",
                       size_hint=(None, None),
                       size=(self.tablero.width*0.5, self.tablero.height*0.4),
                       pos=(self.tablero.width*0.25, self.tablero.height*0.3),
                       opacity=0.55)
            pv.es_preview = True
            self.tablero.add_widget(pv)
        self.lbl_info.text = f"Nivel {getattr(self,'nivel',1)} | {getattr(self,'nombre_dif','')}"
        self.lbl_cuenta.text = f"{self.coloc}/{self.total}"

    def _tick(self, _d):
        self.seg += 1
        self.lbl_t.text = f"{self.seg//60:02d}:{self.seg%60:02d}"

    def _encajo(self, _p):
        self.coloc += 1
        self.lbl_cuenta.text = f"{self.coloc}/{self.total}"
        if self.coloc >= self.total:
            if self.ev:
                self.ev.cancel()
                self.ev = None
            SONIDOS.play(SONIDOS.ganar)
            SONIDOS.play(SONIDOS.voz_ganaste)
            Popup(title="Ganaste!", size_hint=(0.8, 0.5),
                  content=Label(text=f"Nivel {self.nivel}\n{self.nombre_dif}\nTiempo {self.lbl_t.text}")).open()
        else:
            SONIDOS.play(SONIDOS.encaje)


class PuzzleMasterApp(App):
    def build(self):
        self.title = "PuzzleMaster"
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(GameScreen(name="juego"))
        return sm


if __name__ == "__main__":
    PuzzleMasterApp().run()
