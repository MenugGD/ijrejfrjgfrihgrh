#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tournament Maker  -  creado por ZABA

Requisitos:
    pip install PySide6 opencv-python

(opencv-python solo se usa para sacar la miniatura de los archivos .webm;
 sin él todo funciona, pero los .webm se verán con un marcador de posición.)

Ejecutar:
    python tournament_maker.py

OBS:
    Fuente "Captura de ventana" (Windows 10 1903+), ventana "[python.exe]: Tournament Maker".
    El título de la ventana es fijo. Menú Archivo > Para OBS: modo OBS (F10), fondo croma
    y tamaño de ventana 1280x720 / 1600x900 / 1920x1080.
    Al abrir el programa, el cmd muestra la dirección (http://localhost:8765) para pegarla en
    una fuente "Navegador" de OBS. Se puede apagar en Archivo > Para OBS > Fuente de navegador.
"""
import sys
import os
import re
import time
import random
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import shutil
import atexit
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

try:
    from PySide6.QtCore import (Qt, QRectF, QPointF, QPoint, QSize, QTimer, QMimeData, QUrl, Signal,
                                QBuffer, QIODevice)
    from PySide6.QtGui import (QColor, QPainter, QPainterPath, QPen, QFont, QFontMetrics,
                               QPixmap, QImage, QIcon, QLinearGradient, QRadialGradient, QPolygonF, QDrag,
                               QShortcut, QKeySequence, QActionGroup, QRegion)
    from PySide6.QtWidgets import (QApplication, QWidget, QMainWindow, QStackedWidget,
                                   QPushButton, QLineEdit, QDialog, QVBoxLayout, QHBoxLayout,
                                   QSlider, QLabel, QFileDialog, QMessageBox, QMenu,
                                   QToolButton, QScrollArea, QFrame, QGraphicsScene, QGraphicsPixmapItem,
                                   QGraphicsBlurEffect, QSizePolicy, QButtonGroup)
except ImportError:
    print("Falta PySide6.  Instálalo con:  pip install PySide6 opencv-python")
    sys.exit(1)

try:
    from PySide6.QtMultimedia import QMediaPlayer
    from PySide6.QtMultimediaWidgets import QVideoWidget
    HAVE_MM = True
except Exception:
    HAVE_MM = False

try:
    import cv2
except Exception:
    cv2 = None

# ----------------------------------------------------------------------------
# Constantes y utilidades
# ----------------------------------------------------------------------------
ORANGE = "#FF7A1A"
ORANGE_D = "#E8590C"
ORANGE_L = "#FFB070"
INK = "#2B2B2B"
GOLD = "#F5B301"

ROUNDS = [6, 3, 2, 1]                      # casillas por lado en cada ronda
ROUND_NAMES = ["Ronda 1", "Ronda 2", "Semifinal", "Finalista"]
RATIO = 16 / 9                             # proporción de miniatura de YouTube
DESIGN_W, DESIGN_H = 2408, 1260            # tamaño del cuadro a 100 %: casillas de 240x135 px
MIME = "application/x-tournament-slot"
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
VID_EXT = {".webm"}
FILE_FILTER = "Imágenes y video (*.jpg *.jpeg *.png *.webp *.webm);;Todos los archivos (*.*)"
IMG_FILTER = "Imágenes (*.jpg *.jpeg *.png *.webp);;Todos los archivos (*.*)"

TMP = tempfile.mkdtemp(prefix="tournament_maker_")
atexit.register(lambda: shutil.rmtree(TMP, ignore_errors=True))

STYLE = f"""
QWidget {{ font-family: "Segoe UI","Inter","Helvetica Neue","Noto Sans",Arial; color:{INK}; font-size:14px; }}
QDialog, QMessageBox {{ background:#FFFFFF; }}
QPushButton#primary {{ background:{ORANGE}; color:white; border:none; border-radius:20px;
    font-size:18px; font-weight:600; }}
QPushButton#primary:hover {{ background:#FF8D3A; }}
QPushButton#primary:pressed {{ background:{ORANGE_D}; }}
QPushButton#secondary {{ background:white; color:{ORANGE_D}; border:2px solid {ORANGE};
    border-radius:20px; font-size:18px; font-weight:600; }}
QPushButton#secondary:hover {{ background:#FFF1E6; }}
QPushButton#round {{ background:white; border:2px solid {ORANGE}; border-radius:24px; }}
QPushButton#round:hover {{ background:#FFF1E6; }}
QPushButton#round:checked {{ background:{ORANGE}; }}
QPushButton#soft {{ background:#FFF1E6; color:{ORANGE_D}; border:none; border-radius:14px;
    padding:10px 18px; font-weight:600; }}
QPushButton#soft:hover {{ background:#FFE0C7; }}
QPushButton#soft:checked {{ background:{ORANGE}; color:white; }}
QToolButton#file {{ background:rgba(255,255,255,225); border:2px solid {ORANGE}; border-radius:18px;
    padding:7px 18px; font-weight:600; color:{ORANGE_D}; }}
QToolButton#file:hover {{ background:#FFF1E6; }}
QToolButton::menu-indicator {{ image:none; }}
QMenu {{ background:white; border:1px solid #FFD2AE; border-radius:10px; padding:6px; }}
QMenu::item {{ padding:8px 24px; border-radius:8px; }}
QMenu::item:selected {{ background:#FFE6D1; color:{ORANGE_D}; }}
QLineEdit {{ border:2px solid #FFD2AE; border-radius:14px; padding:6px 12px; background:white;
    selection-background-color:{ORANGE}; selection-color:white; }}
QLineEdit:focus {{ border-color:{ORANGE}; }}
QLineEdit:read-only {{ border:2px solid transparent; background:transparent; }}
QSlider::groove:horizontal {{ height:6px; background:#FFE0C7; border-radius:3px; }}
QSlider::sub-page:horizontal {{ background:{ORANGE}; border-radius:3px; }}
QSlider::handle:horizontal {{ background:white; border:2px solid {ORANGE}; width:16px; height:16px;
    margin:-7px 0; border-radius:10px; }}
QScrollBar:horizontal {{ background:rgba(255,255,255,120); height:14px; margin:0 16px; border-radius:7px; }}
QScrollBar:vertical {{ background:rgba(255,255,255,120); width:14px; margin:16px 0; border-radius:7px; }}
QScrollBar::handle:horizontal {{ background:{ORANGE_L}; border-radius:7px; min-width:48px; }}
QScrollBar::handle:vertical {{ background:{ORANGE_L}; border-radius:7px; min-height:48px; }}
QScrollBar::handle:horizontal:hover, QScrollBar::handle:vertical:hover {{ background:{ORANGE}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width:0; height:0; background:none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background:none; }}
"""


def clamp(v, a, b):
    return max(a, min(b, v))


def is_video(path):
    return bool(path) and Path(path).suffix.lower() in VID_EXT


def import_media(path):
    """Copia el archivo a la carpeta temporal de la sesión (así no depende del original)."""
    ext = Path(path).suffix.lower()
    dest = os.path.join(TMP, uuid.uuid4().hex + ext)
    shutil.copy(path, dest)
    return dest


_PM_CACHE = {}


def get_pixmap(path):
    """Devuelve un QPixmap (para .webm, el primer fotograma) o None."""
    if not path:
        return None
    if path in _PM_CACHE:
        return _PM_CACHE[path]
    pm = None
    if is_video(path):
        if cv2 is not None:
            try:
                cap = cv2.VideoCapture(path)
                ok, frame = cap.read()
                cap.release()
                if ok:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, _ = frame.shape
                    img = QImage(frame.data, w, h, 3 * w, QImage.Format_RGB888).copy()
                    pm = QPixmap.fromImage(img)
            except Exception:
                pm = None
    else:
        q = QPixmap(path)
        if q.isNull() and cv2 is not None:
            try:
                import numpy as np
                arr = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
                if arr is not None:
                    arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
                    h, w, _ = arr.shape
                    q = QPixmap.fromImage(QImage(arr.data, w, h, 3 * w, QImage.Format_RGB888).copy())
            except Exception:
                pass
        pm = q if not q.isNull() else None
    _PM_CACHE[path] = pm
    return pm


_THUMB_CACHE = {}


def get_thumb(path, max_w=1100):
    """Versión reducida (y cacheada) para pintar las casillas sin que se trabe."""
    pm = get_pixmap(path)
    if pm is None or pm.width() <= max_w:
        return pm
    th = _THUMB_CACHE.get(path)
    if th is None:
        th = pm.scaledToWidth(max_w, Qt.SmoothTransformation)
        _THUMB_CACHE[path] = th
    return th


def natural_key(p):
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", Path(p).name)]


def crop_source(pw, ph, aspect, fx=0.5, fy=0.5, zoom=1.0):
    """Zona (en píxeles de la imagen) que se ve en una casilla de proporción 'aspect'."""
    if pw / ph > aspect:
        h0, w0 = ph, ph * aspect
    else:
        w0, h0 = pw, pw / aspect
    z = max(1.0, zoom)
    w, h = w0 / z, h0 / z
    x = clamp(fx * pw - w / 2, 0, pw - w)
    y = clamp(fy * ph - h / 2, 0, ph - h)
    return QRectF(x, y, w, h)


def draw_cover(qp, pm, r, fx=0.5, fy=0.5, zoom=1.0):
    """Dibuja pm llenando el rectángulo r, mostrando solo la zona de recorte elegida."""
    src = crop_source(pm.width(), pm.height(), r.width() / r.height(), fx, fy, zoom)
    qp.drawPixmap(r, pm, src)


def blur_pixmap(pm, radius):
    if radius <= 0:
        return pm
    item = QGraphicsPixmapItem(pm)
    eff = QGraphicsBlurEffect()
    eff.setBlurRadius(radius)
    eff.setBlurHints(QGraphicsBlurEffect.QualityHint)
    item.setGraphicsEffect(eff)
    scene = QGraphicsScene()
    scene.addItem(item)
    img = QImage(pm.size(), QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    scene.render(p, QRectF(img.rect()), QRectF(0, 0, pm.width(), pm.height()))
    p.end()
    pad = int(min(radius * 1.5, min(pm.width(), pm.height()) // 4))
    return QPixmap.fromImage(img.copy(pad, pad, img.width() - 2 * pad, img.height() - 2 * pad))


def pencil_icon(color=ORANGE, size=64):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.translate(size / 2, size / 2)
    p.rotate(45)
    s = size
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    p.drawRoundedRect(QRectF(-s * 0.09, -s * 0.40, s * 0.18, s * 0.58), 3, 3)
    p.drawPolygon(QPolygonF([QPointF(-s * 0.09, s * 0.18), QPointF(s * 0.09, s * 0.18),
                             QPointF(0, s * 0.40)]))
    p.setBrush(QColor("white"))
    p.drawRect(QRectF(-s * 0.09, -s * 0.27, s * 0.18, s * 0.04))
    p.end()
    return QIcon(pm)


def camera_icon(color=ORANGE, size=64):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    p.drawRoundedRect(QRectF(s * 0.14, s * 0.30, s * 0.72, s * 0.46), s * 0.09, s * 0.09)
    p.drawRoundedRect(QRectF(s * 0.34, s * 0.20, s * 0.22, s * 0.14), s * 0.04, s * 0.04)
    p.setBrush(QColor("white"))
    p.drawEllipse(QPointF(s * 0.5, s * 0.53), s * 0.16, s * 0.16)
    p.setBrush(QColor(color))
    p.drawEllipse(QPointF(s * 0.5, s * 0.53), s * 0.10, s * 0.10)
    p.setBrush(QColor("white"))
    p.drawEllipse(QPointF(s * 0.76, s * 0.39), s * 0.028, s * 0.028)
    p.end()
    return QIcon(pm)


def bracket_centers(top, bottom):
    """Centros verticales de cada casilla de un lado: {(ronda, i): y}."""
    pitch = (bottom - top) / 6.0
    r0 = [top + pitch * (i + 0.5) for i in range(6)]
    r1 = [(r0[0] + r0[1]) / 2, (r0[2] + r0[3]) / 2, (r0[4] + r0[5]) / 2]
    r2 = [(r1[0] + r1[1]) / 2, r1[2]]
    r3 = [(r2[0] + r2[1]) / 2]
    out = {}
    for r, lst in enumerate([r0, r1, r2, r3]):
        for i, y in enumerate(lst):
            out[(r, i)] = y
    return out


def bracket_links():
    """Pares (origen, destino) de casillas conectadas por líneas."""
    links = []
    for side in "LR":
        for r in range(3):
            for i in range(ROUNDS[r]):
                links.append(((side, r, i), (side, r + 1, i // 2)))
        links.append(((side, 3, 0), ("C", 0, 0)))
    return links


def elbow(qp, a, b):
    """Dibuja una línea en ángulo recto entre los rectángulos a y b."""
    right = a.center().x() < b.center().x()
    x1 = a.right() if right else a.left()
    x2 = b.left() if right else b.right()
    y1, y2 = a.center().y(), b.center().y()
    mx = (x1 + x2) / 2
    path = QPainterPath()
    path.moveTo(x1, y1)
    path.lineTo(mx, y1)
    path.lineTo(mx, y2)
    path.lineTo(x2, y2)
    qp.setBrush(Qt.NoBrush)
    qp.drawPath(path)


def draw_pill(qp, cx, y, maxw, text, bold=False, fg=INK, alpha=225, h=22, size=13):
    f = QFont(qp.font())
    f.setPixelSize(size)
    f.setBold(bold)
    qp.setFont(f)
    fm = QFontMetrics(f)
    t = fm.elidedText(text, Qt.ElideRight, int(max(10, maxw - 22)))
    w = min(maxw, fm.horizontalAdvance(t) + 22)
    r = QRectF(cx - w / 2, y, w, h)
    qp.setPen(Qt.NoPen)
    qp.setBrush(QColor(255, 255, 255, alpha))
    qp.drawRoundedRect(r, h / 2, h / 2)
    qp.setPen(QColor(fg))
    qp.drawText(r, Qt.AlignCenter, t)


@dataclass
class Participant:
    name: str = ""
    detail: str = ""
    media: str = ""
    fx: float = 0.5        # centro del recorte de la miniatura (0..1)
    fy: float = 0.5
    zoom: float = 1.0      # 1 = recorte automático; >1 = acercar


# ----------------------------------------------------------------------------
# Casilla de participante
# ----------------------------------------------------------------------------
def text_heights(k):
    """Alturas (nombre, detalle, separación) de los textos de una casilla según la escala."""
    return max(12, int(20 * k)), max(12, int(20 * k)), max(2, int(3 * k))


class SlotWidget(QWidget):
    def __init__(self, canvas, key):
        super().__init__(canvas)
        self.canvas = canvas
        self.key = key
        self.k = 1.0
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self._hover = False
        self._drop = False
        self._press = None
        self._press_g = None
        self._panning = False

    @property
    def part(self):
        return self.canvas.state[self.key]

    @property
    def is_champ(self):
        return self.key[0] == "C"

    def img_rect(self):
        nh, dh, gp = text_heights(self.k)
        return QRectF(0, nh + gp, self.width(), max(4, self.height() - nh - dh - 2 * gp))

    # ---------------- pintura ----------------
    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setRenderHints(QPainter.RenderHint.Antialiasing |
                          QPainter.RenderHint.SmoothPixmapTransform |
                          QPainter.RenderHint.TextAntialiasing)
        k = self.k
        nh, dh, _ = text_heights(k)
        ps = max(8, int(13 * k))
        bw = max(0.7, k)
        r = self.img_rect()
        part = self.part
        path = QPainterPath()
        rad = max(6.0, 14 * k)
        path.addRoundedRect(r, rad, rad)
        accent = QColor(GOLD if self.is_champ else ORANGE)

        if part is None:
            qp.setPen(QPen(accent, max(1.2, 2 * k), Qt.DashLine))
            qp.setBrush(QColor(255, 255, 255, 235 if self._hover else 175))
            qp.drawPath(path)
            if self.is_champ:
                f = QFont(qp.font())
                f.setPixelSize(max(8, int(14 * k)))
                f.setBold(True)
                qp.setFont(f)
                qp.setPen(QColor(ORANGE_D))
                qp.drawText(r.adjusted(6, 0, -6, 0), Qt.AlignCenter | Qt.TextWordWrap,
                            "Arrastra aquí\nal ganador")
            else:
                c = r.center()
                s = min(r.width(), r.height()) * 0.13
                qp.setPen(QPen(accent, max(2.0, 3 * k), Qt.SolidLine, Qt.RoundCap))
                qp.drawLine(QPointF(c.x() - s, c.y()), QPointF(c.x() + s, c.y()))
                qp.drawLine(QPointF(c.x(), c.y() - s), QPointF(c.x(), c.y() + s))
        else:
            status = self.canvas.slot_status(self.key)
            alone = status is not None
            qp.save()
            qp.setClipPath(path)
            pm = get_thumb(part.media)
            if pm is not None:
                draw_cover(qp, pm, r, part.fx, part.fy, part.zoom)
            else:
                qp.fillPath(path, QColor("#FFE6D1"))
                qp.setPen(QColor(ORANGE_D))
                qp.drawText(r, Qt.AlignCenter, "WEBM" if is_video(part.media) else "Sin imagen")
            if alone:
                qp.fillRect(r, QColor(90, 90, 90, 205) if status == "elim" else QColor(110, 110, 110, 180))
                f = QFont(qp.font())
                f.setPixelSize(max(7, int(12 * k)))
                f.setBold(True)
                qp.setFont(f)
                qp.setPen(QColor(255, 255, 255, 230))
                qp.drawText(r, Qt.AlignCenter, "ELIMINADO" if status == "elim" else "SIN RIVAL")
            qp.restore()
            qp.setPen(QPen(accent, (3 if self.is_champ else 2) * bw))
            qp.setBrush(Qt.NoBrush)
            qp.drawPath(path)
            fg = "#777777" if alone else INK
            cx = self.width() / 2
            if part.name:
                draw_pill(qp, cx, 0, self.width(), part.name, bold=True, fg=fg, h=nh, size=ps)
            if part.detail:
                draw_pill(qp, cx, self.height() - dh, self.width(), part.detail,
                          fg="#666666", h=dh, size=max(7, ps - 1))

        if self._drop:
            qp.setPen(QPen(QColor(ORANGE_D), 4 * bw))
            qp.setBrush(QColor(255, 122, 26, 45))
            qp.drawPath(path)

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    # ---------------- ratón ----------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press = e.position().toPoint()
            self._press_g = e.globalPosition().toPoint()
            self._panning = False
        else:
            e.ignore()                 # botón central: lo recibe el cuadro y desplaza la vista

    def mouseMoveEvent(self, e):
        if self._panning:
            self.canvas.pan_to(e.globalPosition().toPoint())
            return
        if self._press is None or not (e.buttons() & Qt.LeftButton):
            return
        if (e.position().toPoint() - self._press).manhattanLength() < QApplication.startDragDistance():
            return
        if self.part is None:          # casilla vacía: arrastrar mueve la vista
            self._panning = True
            self._press = None
            self.canvas.start_pan(self._press_g)
            self.canvas.pan_to(e.globalPosition().toPoint())
            return
        self._press = None
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME, ",".join(str(x) for x in self.key).encode())
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(e.position().toPoint())
        drag.exec(Qt.MoveAction)

    def mouseReleaseEvent(self, e):
        if self._panning:
            self._panning = False
            self.canvas.end_pan()
            return
        if e.button() == Qt.LeftButton and self._press is not None:
            self._press = None
            if self.rect().contains(e.position().toPoint()):
                if self.part is None:
                    if not self.is_champ:
                        self.canvas.pick_file(self.key)
                else:
                    self.canvas.open_preview(self.key)

    def contextMenuEvent(self, e):
        if self.part is None:
            return
        m = QMenu(self)
        a_view = m.addAction("Ver / editar")
        a_crop = m.addAction("Ajustar miniatura…")
        a_img = m.addAction("Cambiar imagen")
        a_el = None
        if not self.is_champ:
            elim = self.key in self.canvas.eliminated
            a_el = m.addAction("Quitar gris (eliminado)" if elim else "Marcar como eliminado")
        m.addSeparator()
        a_clear = m.addAction("Vaciar casilla")
        act = m.exec(e.globalPos())
        if act is None:
            return
        if act == a_view:
            self.canvas.open_preview(self.key)
        elif act == a_crop:
            self.canvas.open_preview(self.key, True)
        elif act == a_img:
            self.canvas.pick_file(self.key)
        elif a_el is not None and act == a_el:
            self.canvas.toggle_eliminated(self.key)
        elif act == a_clear:
            self.canvas.state[self.key] = None
            self.canvas.eliminated.discard(self.key)
            self.canvas.refresh()
            self.canvas.changed.emit()

    # ---------------- arrastrar y soltar ----------------
    @staticmethod
    def _src_key(e):
        if e.mimeData().hasFormat(MIME):
            s, r, i = bytes(e.mimeData().data(MIME)).decode().split(",")
            return (s, int(r), int(i))
        return None

    def _accepts(self, e):
        k = self._src_key(e)
        if k:
            return self.canvas.drop_kind(k, self.key) is not None
        if e.mimeData().hasUrls() and not self.is_champ:
            urls = e.mimeData().urls()
            if urls:
                ext = Path(urls[0].toLocalFile()).suffix.lower()
                return ext in IMG_EXT or ext in VID_EXT
        return False

    def dragEnterEvent(self, e):
        if self._accepts(e):
            self._drop = True
            e.acceptProposedAction()
            self.update()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        self.canvas.autoscroll(self.mapToGlobal(e.position().toPoint()))
        if self._accepts(e):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragLeaveEvent(self, e):
        self._drop = False
        self.update()

    def dropEvent(self, e):
        self._drop = False
        k = self._src_key(e)
        if k:
            self.canvas.perform_drop(k, self.key)
        elif e.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
            if len(paths) > 1:
                self.canvas.import_many(paths)
            elif paths:
                self.canvas.assign_file(self.key, paths[0])
        e.acceptProposedAction()
        self.update()


# ----------------------------------------------------------------------------
# Widgets auxiliares
# ----------------------------------------------------------------------------
class FitImage(QWidget):
    """Muestra la imagen completa (sin recortar) centrada en su área."""

    def __init__(self, pm):
        super().__init__()
        self.pm = pm
        self.setMinimumSize(160, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform |
                          QPainter.RenderHint.TextAntialiasing)
        r = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(r, 20, 20)
        qp.fillPath(path, QColor("#FFF4EA"))
        if self.pm is None:
            qp.setPen(QColor(ORANGE_D))
            qp.drawText(r, Qt.AlignCenter, "Sin vista previa")
            return
        qp.setClipPath(path)
        pw, ph = self.pm.width(), self.pm.height()
        s = min(r.width() / pw, r.height() / ph)
        dw, dh = pw * s, ph * s
        target = QRectF(r.center().x() - dw / 2, r.center().y() - dh / 2, dw, dh)
        qp.drawPixmap(target, self.pm, QRectF(self.pm.rect()))


class CropEditor(QWidget):
    """Muestra la imagen completa y un recuadro 16:9 que se mueve/zoomea: es lo que verá la casilla."""
    changed = Signal()

    def __init__(self, part, pm):
        super().__init__()
        self.part = part
        self.pm = pm
        self._drag = None
        self.setMinimumSize(160, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setCursor(Qt.OpenHandCursor)

    def _geom(self):
        r = QRectF(self.rect())
        pw, ph = self.pm.width(), self.pm.height()
        s = min(r.width() / pw, r.height() / ph)
        ir = QRectF(r.center().x() - pw * s / 2, r.center().y() - ph * s / 2, pw * s, ph * s)
        src = crop_source(pw, ph, RATIO, self.part.fx, self.part.fy, self.part.zoom)
        cr = QRectF(ir.x() + src.x() * s, ir.y() + src.y() * s, src.width() * s, src.height() * s)
        return ir, cr, s

    def sync(self):
        """Deja fx/fy dentro de rango según el zoom actual."""
        pw, ph = self.pm.width(), self.pm.height()
        src = crop_source(pw, ph, RATIO, self.part.fx, self.part.fy, self.part.zoom)
        self.part.fx = src.center().x() / pw
        self.part.fy = src.center().y() / ph
        self.update()

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 20, 20)
        qp.fillPath(path, QColor("#FFF4EA"))
        qp.setClipPath(path)
        ir, cr, s = self._geom()
        qp.drawPixmap(ir, self.pm, QRectF(self.pm.rect()))
        dim = QPainterPath()
        dim.addRect(ir)
        hole = QPainterPath()
        hole.addRoundedRect(cr, 8, 8)
        qp.fillPath(dim.subtracted(hole), QColor(0, 0, 0, 150))
        qp.setBrush(Qt.NoBrush)
        qp.setPen(QPen(QColor(255, 255, 255, 110), 1))
        for k in (1, 2):
            qp.drawLine(QPointF(cr.left() + cr.width() * k / 3, cr.top()),
                        QPointF(cr.left() + cr.width() * k / 3, cr.bottom()))
            qp.drawLine(QPointF(cr.left(), cr.top() + cr.height() * k / 3),
                        QPointF(cr.right(), cr.top() + cr.height() * k / 3))
        qp.setPen(QPen(QColor("white"), 5))
        qp.drawRoundedRect(cr, 8, 8)
        qp.setPen(QPen(QColor(ORANGE), 3))
        qp.drawRoundedRect(cr, 8, 8)

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        pos = e.position()
        ir, cr, s = self._geom()
        if ir.contains(pos) and not cr.contains(pos):      # clic fuera del recuadro: centrarlo ahí
            self.part.fx = clamp((pos.x() - ir.x()) / ir.width(), 0, 1)
            self.part.fy = clamp((pos.y() - ir.y()) / ir.height(), 0, 1)
            self.sync()
            self.changed.emit()
        self._drag = (pos, self.part.fx, self.part.fy)
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if self._drag is None:
            return
        ir, cr, s = self._geom()
        p0, fx0, fy0 = self._drag
        d = e.position() - p0
        self.part.fx = fx0 + d.x() / ir.width()
        self.part.fy = fy0 + d.y() / ir.height()
        self.sync()
        self.changed.emit()

    def mouseReleaseEvent(self, e):
        self._drag = None
        self.setCursor(Qt.OpenHandCursor)

    def wheelEvent(self, e):
        f = 1.12 if e.angleDelta().y() > 0 else 1 / 1.12
        self.part.zoom = clamp(self.part.zoom * f, 1.0, 5.0)
        self.sync()
        self.changed.emit()
        e.accept()


class PreviewOverlay(QWidget):
    """Vista previa a pantalla completa dentro de la misma ventana (como al abrir un post)."""
    closed = Signal(bool)

    def __init__(self, parent):
        super().__init__(parent)
        self.part = None
        self.modified = False
        self.player = None
        self.crop_editor = None
        self.setFocusPolicy(Qt.StrongFocus)

        self.card = QFrame(self)
        self.card.setObjectName("previewcard")
        self.card.setStyleSheet("QFrame#previewcard { background:white; border-radius:26px; }")
        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(24, 24, 24, 18)
        lay.setSpacing(12)
        self.media_host = QVBoxLayout()
        lay.addLayout(self.media_host, 1)

        # barra de ajuste de miniatura
        self.crop_bar = QWidget()
        cb = QVBoxLayout(self.crop_bar)
        cb.setContentsMargins(0, 0, 0, 0)
        cb.setSpacing(6)
        hint = QLabel("Arrastra el recuadro para elegir el corte de la miniatura · rueda o deslizador para acercar")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:#8C8C8C; font-size:13px;")
        cb.addWidget(hint)
        crow = QHBoxLayout()
        lbl = QLabel("Zoom")
        lbl.setStyleSheet(f"color:{ORANGE_D}; font-weight:600;")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(100, 500)
        self.btn_reset = QPushButton("Restablecer")
        self.btn_reset.setObjectName("soft")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        crow.addWidget(lbl)
        crow.addWidget(self.zoom_slider, 1)
        crow.addWidget(self.btn_reset)
        cb.addLayout(crow)
        self.crop_bar.hide()
        lay.addWidget(self.crop_bar)

        self.name = QLineEdit()
        self.name.setAlignment(Qt.AlignCenter)
        self.name.setStyleSheet("font-size:26px; font-weight:700;")
        self.name.setReadOnly(True)
        self.detail = QLineEdit()
        self.detail.setAlignment(Qt.AlignCenter)
        self.detail.setStyleSheet("font-size:16px; color:#666666;")
        self.detail.setReadOnly(True)
        lay.addWidget(self.name)
        lay.addWidget(self.detail)

        row = QHBoxLayout()
        self.btn_pen = QPushButton()
        self.btn_pen.setObjectName("round")
        self.btn_pen.setCheckable(True)
        self.btn_pen.setFixedSize(48, 48)
        self.btn_pen.setIcon(pencil_icon(ORANGE))
        self.btn_pen.setIconSize(self.btn_pen.size() * 0.55)
        self.btn_pen.setToolTip("Editar detalles")
        self.btn_pen.setCursor(Qt.PointingHandCursor)
        self.btn_img = QPushButton("Cambiar imagen")
        self.btn_img.setObjectName("soft")
        self.btn_img.setCursor(Qt.PointingHandCursor)
        self.btn_img.hide()
        self.btn_crop = QPushButton("Ajustar miniatura")
        self.btn_crop.setObjectName("soft")
        self.btn_crop.setCheckable(True)
        self.btn_crop.setCursor(Qt.PointingHandCursor)
        self.btn_crop.hide()
        row.addStretch()
        row.addWidget(self.btn_pen)
        row.addWidget(self.btn_img)
        row.addWidget(self.btn_crop)
        row.addStretch()
        lay.addLayout(row)

        self.btn_close = QPushButton("×", self)
        self.btn_close.setFixedSize(46, 46)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setToolTip("Cerrar (Esc)")
        self.btn_close.setStyleSheet(
            "QPushButton { background:rgba(255,255,255,235); color:#E8590C; border:none; "
            "border-radius:23px; font-size:30px; font-weight:600; padding-bottom:3px; }"
            "QPushButton:hover { background:white; }")
        self.btn_close.clicked.connect(self.close_overlay)

        self.btn_pen.toggled.connect(self.set_editing)
        self.btn_img.clicked.connect(self.change_image)
        self.btn_crop.toggled.connect(self.set_crop_mode)
        self.btn_reset.clicked.connect(self.reset_crop)
        self.zoom_slider.valueChanged.connect(self._zoom_slider)
        self.name.textEdited.connect(self._name_edited)
        self.detail.textEdited.connect(self._detail_edited)
        self.hide()

    # ----- ciclo de vida -----
    def show_for(self, part, crop=False):
        self.part = part
        self.modified = False
        self.name.setText(part.name)
        self.detail.setText(part.detail)
        self.btn_crop.setChecked(False)
        self.btn_pen.setChecked(False)
        self.set_editing(False)
        self.crop_bar.hide()
        self.build_media()
        if crop:
            self.btn_pen.setChecked(True)
            self.btn_crop.setChecked(True)
        self.relayout()
        self.show()
        self.raise_()
        self.setFocus()

    def close_overlay(self):
        if not self.isVisible():
            return
        self.clear_media()
        self.hide()
        mod = self.modified
        self.part = None
        self.closed.emit(mod)

    def relayout(self):
        p = self.parentWidget()
        self.setGeometry(0, 0, p.width(), p.height())
        W, H = self.width(), self.height()
        cw = int(min(1200, W * 0.92))
        ch = int(min(960, H * 0.94))
        self.card.setGeometry((W - cw) // 2, (H - ch) // 2, cw, ch)
        self.btn_close.move(W - 46 - 18, 18)
        self.btn_close.raise_()

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.fillRect(self.rect(), QColor(12, 12, 12, 195))

    def mousePressEvent(self, e):
        if not self.card.geometry().contains(e.position().toPoint()):
            self.close_overlay()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close_overlay()
        else:
            super().keyPressEvent(e)

    # ----- edición -----
    def _name_edited(self, t):
        if self.part is not None:
            self.part.name = t
            self.modified = True

    def _detail_edited(self, t):
        if self.part is not None:
            self.part.detail = t
            self.modified = True

    def set_editing(self, on):
        self.name.setReadOnly(not on)
        self.detail.setReadOnly(not on)
        self.detail.setPlaceholderText("Detalles…" if on else "")
        self.btn_img.setVisible(on)
        self.btn_crop.setVisible(on)
        if not on:
            self.btn_crop.setChecked(False)
        elif not self.btn_crop.isChecked():
            self.name.setFocus()
            self.name.selectAll()
        self.btn_pen.setIcon(pencil_icon("white" if on else ORANGE))

    # ----- ajuste de la miniatura -----
    def set_crop_mode(self, on):
        self.crop_bar.setVisible(on)
        if self.part is None:
            return
        if on:
            self._set_slider(self.part.zoom)
        self.build_media()

    def _set_slider(self, z):
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(round(z * 100)))
        self.zoom_slider.blockSignals(False)

    def _zoom_slider(self, v):
        if self.part is None:
            return
        self.part.zoom = v / 100.0
        self.modified = True
        if self.crop_editor is not None:
            self.crop_editor.sync()

    def _crop_changed(self):
        self.modified = True
        if self.part is not None:
            self._set_slider(self.part.zoom)

    def reset_crop(self):
        if self.part is None:
            return
        self.part.fx, self.part.fy, self.part.zoom = 0.5, 0.5, 1.0
        self.modified = True
        self._set_slider(1.0)
        if self.crop_editor is not None:
            self.crop_editor.sync()

    # ----- medios -----
    def clear_media(self):
        self.crop_editor = None
        if self.player is not None:
            self.player.stop()
            self.player.setSource(QUrl())
            self.player.deleteLater()
            self.player = None
        while self.media_host.count():
            it = self.media_host.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    def build_media(self):
        self.clear_media()
        if self.part is None:
            return
        path = self.part.media
        pm = get_pixmap(path)
        if self.btn_crop.isChecked() and pm is not None:
            self.crop_editor = CropEditor(self.part, pm)
            self.crop_editor.changed.connect(self._crop_changed)
            self.media_host.addWidget(self.crop_editor)
        elif is_video(path) and HAVE_MM:
            vw = QVideoWidget()
            vw.setMinimumHeight(160)
            self.media_host.addWidget(vw)
            self.player = QMediaPlayer(self)
            self.player.setVideoOutput(vw)
            self.player.setSource(QUrl.fromLocalFile(path))
            try:
                self.player.setLoops(QMediaPlayer.Loops.Infinite)
            except Exception:
                pass
            self.player.play()
        else:
            self.media_host.addWidget(FitImage(pm))

    def change_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecciona imagen o video", "", FILE_FILTER)
        if path and self.part is not None:
            self.part.media = import_media(path)
            self.part.fx, self.part.fy, self.part.zoom = 0.5, 0.5, 1.0
            self._set_slider(1.0)
            self.modified = True
            self.build_media()


class BackgroundDialog(QDialog):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self._orig = (canvas.bg_path, canvas.bg_blur, canvas.bg_veil)
        self.setWindowTitle("Fondo personalizado")
        self.setFixedWidth(430)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 24, 26, 22)
        lay.setSpacing(10)

        row = QHBoxLayout()
        b1 = QPushButton("Elegir imagen…")
        b1.setObjectName("soft")
        b2 = QPushButton("Quitar fondo")
        b2.setObjectName("soft")
        row.addWidget(b1)
        row.addWidget(b2)
        lay.addLayout(row)

        self.lbl_blur = QLabel()
        self.s_blur = QSlider(Qt.Horizontal)
        self.s_blur.setRange(0, 40)
        self.s_blur.setValue(canvas.bg_blur)
        self.lbl_veil = QLabel()
        self.s_veil = QSlider(Qt.Horizontal)
        self.s_veil.setRange(0, 90)
        self.s_veil.setValue(canvas.bg_veil)
        for w in (self.lbl_blur, self.s_blur, self.lbl_veil, self.s_veil):
            lay.addWidget(w)

        row2 = QHBoxLayout()
        row2.addStretch()
        cancel = QPushButton("Cancelar")
        cancel.setObjectName("secondary")
        ok = QPushButton("Aceptar")
        ok.setObjectName("primary")
        for b in (cancel, ok):
            b.setFixedSize(120, 42)
            b.setStyleSheet("font-size:15px;")
            row2.addWidget(b)
        lay.addSpacing(6)
        lay.addLayout(row2)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.apply)
        self.s_blur.valueChanged.connect(self._slider)
        self.s_veil.valueChanged.connect(self._slider)
        b1.clicked.connect(self.choose)
        b2.clicked.connect(self.remove)
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        self._labels()

    def _labels(self):
        self.lbl_blur.setText(f"Desenfoque (blur): {self.s_blur.value()}")
        self.lbl_veil.setText(f"Velo blanco (legibilidad): {self.s_veil.value()}%")

    def _slider(self):
        self._labels()
        self._timer.start(90)

    def apply(self):
        self.canvas.set_background(self.canvas.bg_path, self.s_blur.value(), self.s_veil.value())

    def choose(self):
        path, _ = QFileDialog.getOpenFileName(self, "Imagen de fondo", "", IMG_FILTER)
        if path:
            self.canvas.set_background(import_media(path), self.s_blur.value(), self.s_veil.value())

    def remove(self):
        self.canvas.set_background("", self.s_blur.value(), self.s_veil.value())

    def accept(self):
        self.apply()
        self.canvas.changed.emit()
        super().accept()

    def reject(self):
        self.canvas.set_background(*self._orig)
        super().reject()


# ----------------------------------------------------------------------------
# Panel del torneo
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Cinemática del campeón (espacio libre arriba al centro del cuadro)
# ----------------------------------------------------------------------------
FIREWORK_COLORS = ["#FFB347", "#FF7A1A", "#FFD84D", "#FFFFFF", "#FF5E8A", "#7FE3FF", "#B38CFF", "#7CFFB2"]


def ease_out_back(x):
    x = clamp(x, 0.0, 1.0)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


class _Rocket:
    __slots__ = ("x", "y", "vy", "ty", "color")


class _Spark:
    __slots__ = ("x", "y", "px", "py", "vx", "vy", "life", "max", "color", "size")


def _spark(x, y, vx, vy, life, color, size):
    s = _Spark()
    s.x = s.px = x
    s.y = s.py = y
    s.vx, s.vy = vx, vy
    s.life = s.max = life
    s.color = color
    s.size = size
    return s


class ChampionStage(QWidget):
    """Panel tipo cine con la imagen del campeón en grande y fuegos artificiales."""
    DURATION = 9.0
    SCHEDULE = [0.3, 0.7, 1.1, 1.5, 1.9, 2.3, 2.7, 3.1, 3.5, 3.8, 4.2, 4.6, 5.0, 5.5, 6.0, 6.6, 7.2, 7.8]

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.T = None                      # None = estático (sin animación)
        self.rockets = []
        self.sparks = []
        self.pending = []
        self._last = 0.0
        self._press = None
        self._press_g = None
        self._panning = False
        rnd = random.Random(7)
        self.stars = [(rnd.random(), rnd.random(), rnd.uniform(0.6, 1.8), rnd.uniform(0, 6.28))
                      for _ in range(46)]
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)
        self.setToolTip("Clic para repetir la animación")
        self.setCursor(Qt.PointingHandCursor)
        self.hide()

    def champion(self):
        return self.canvas.state.get(("C", 0, 0))

    def sync(self):
        """Se llama cada vez que cambia el cuadro: muestra u oculta el panel."""
        if self.champion() is None:
            self.timer.stop()
            self.T = None
            self.rockets, self.sparks, self.pending = [], [], []
            self.hide()
        else:
            self.show()
            self.update()

    def play(self):
        if self.champion() is None:
            return
        self.show()
        self.raise_()
        self.T = 0.0
        self.rockets, self.sparks = [], []
        self.pending = list(self.SCHEDULE)
        self._last = time.perf_counter()
        self.timer.start()
        self.update()

    # ---------------- simulación ----------------
    def _launch(self):
        W, H = max(1, self.width()), max(1, self.height())
        r = _Rocket()
        r.x = random.uniform(W * 0.1, W * 0.9)
        r.y = H * 0.98
        r.ty = random.uniform(H * 0.12, H * 0.5)
        r.vy = -random.uniform(H * 0.9, H * 1.3)
        r.color = QColor(random.choice(FIREWORK_COLORS))
        self.rockets.append(r)

    def _explode(self, x, y, color):
        if len(self.sparks) > 1800:
            return
        W, H = max(1, self.width()), max(1, self.height())
        n = random.randint(55, 85)
        base = min(W, H) * random.uniform(0.55, 0.85)
        ring = random.random() < 0.35
        second = QColor(random.choice(FIREWORK_COLORS)) if random.random() < 0.4 else color
        for i in range(n):
            a = 2 * math.pi * i / n + random.uniform(-0.05, 0.05)
            sp = base * (0.85 if ring else random.uniform(0.25, 1.0))
            self.sparks.append(_spark(x, y, math.cos(a) * sp, math.sin(a) * sp,
                                      random.uniform(1.0, 1.7), color if i % 2 == 0 else second,
                                      random.uniform(1.6, 3.0)))

    def _tick(self):
        now = time.perf_counter()
        dt = min(0.05, max(0.0, now - self._last))
        self._last = now
        if self.T is None:
            self.timer.stop()
            return
        self.T += dt
        H = max(1, self.height())
        while self.pending and self.pending[0] <= self.T:
            self.pending.pop(0)
            self._launch()
        for r in self.rockets[:]:
            r.y += r.vy * dt
            if len(self.sparks) < 1800 and random.random() < 0.7:       # estela del cohete
                self.sparks.append(_spark(r.x + random.uniform(-1, 1), r.y, random.uniform(-15, 15),
                                          random.uniform(20, 60), 0.35, QColor("#FFC070"), 1.6))
            if r.y <= r.ty:
                self.rockets.remove(r)
                self._explode(r.x, r.y, r.color)
        g = H * 0.5
        damp = 1 - 1.5 * dt
        for s in self.sparks:
            s.px, s.py = s.x, s.y
            s.vx *= damp
            s.vy = s.vy * damp + g * dt
            s.x += s.vx * dt
            s.y += s.vy * dt
            s.life -= dt
        self.sparks = [s for s in self.sparks if s.life > 0]
        if self.T > self.DURATION and not self.rockets and not self.sparks and not self.pending:
            self.T = None
            self.timer.stop()
        self.update()

    # ---------------- pintura ----------------
    def paintEvent(self, e):
        champ = self.champion()
        if champ is None:
            return
        qp = QPainter(self)
        qp.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform |
                          QPainter.RenderHint.TextAntialiasing)
        W, H = float(self.width()), float(self.height())
        ui = self.canvas.ui
        anim = self.T is not None
        t = self.T if anim else 99.0

        panel = QPainterPath()
        rad = clamp(30 * ui, 10, 70)
        panel.addRoundedRect(QRectF(0.5, 0.5, W - 1, H - 1), rad, rad)
        g = QLinearGradient(0, 0, 0, H)
        g.setColorAt(0.0, QColor("#150E2B"))
        g.setColorAt(0.65, QColor("#2A1226"))
        g.setColorAt(1.0, QColor("#40190A"))
        qp.fillPath(panel, g)
        qp.setClipPath(panel)

        qp.setPen(Qt.NoPen)                                   # estrellas de fondo
        for sx, sy, sr, ph in self.stars:
            tw = 0.55 + 0.45 * math.sin(t * 2.2 + ph) if anim else 0.6
            qp.setBrush(QColor(255, 240, 210, int(110 * tw)))
            qp.drawEllipse(QPointF(sx * W, sy * H), sr * ui * 1.2 + 0.5, sr * ui * 1.2 + 0.5)

        title_h, name_h = H * 0.17, H * 0.15
        area = QRectF(W * 0.06, title_h, W * 0.88, H - title_h - name_h)
        pm = get_thumb(champ.media, 1600)
        if pm is not None:
            s0 = min(area.width() / pm.width(), area.height() / pm.height())
            iw, ih = pm.width() * s0, pm.height() * s0
        else:
            ih = area.height()
            iw = ih * RATIO
        scale = 0.25 + 0.75 * ease_out_back(t / 1.0)
        op = clamp(t / 0.5, 0.0, 1.0)
        c = area.center()
        ir = QRectF(c.x() - iw * scale / 2, c.y() - ih * scale / 2, iw * scale, ih * scale)

        pulse = 1.0 + 0.05 * math.sin(t * 3) if anim else 1.0   # foco dorado detrás de la imagen
        rg = QRadialGradient(c, max(W, H) * 0.55 * pulse)
        rg.setColorAt(0.0, QColor(255, 200, 90, int(120 * op)))
        rg.setColorAt(1.0, QColor(255, 200, 90, 0))
        qp.fillRect(QRectF(0, 0, W, H), rg)

        # imagen con marco dorado
        ri = clamp(16 * ui, 6, 40)
        qp.save()
        qp.setOpacity(op)
        qp.setBrush(Qt.NoBrush)
        for k, a in ((3, 40), (2, 70), (1, 110)):
            qp.setPen(QPen(QColor(255, 200, 80, a), (k * 5 + 4) * ui))
            qp.drawRoundedRect(ir, ri, ri)
        frame = QPainterPath()
        frame.addRoundedRect(ir, ri, ri)
        qp.setClipPath(frame, Qt.IntersectClip)
        if pm is not None:
            qp.drawPixmap(ir, pm, QRectF(pm.rect()))
        else:
            qp.fillPath(frame, QColor("#FFE6D1"))
        qp.restore()
        qp.save()
        qp.setOpacity(op)
        qp.setBrush(Qt.NoBrush)
        qp.setPen(QPen(QColor(GOLD), max(2.0, 4 * ui)))
        qp.drawRoundedRect(ir, ri, ri)
        qp.restore()

        # textos
        ta = clamp((t - 0.45) / 0.5, 0.0, 1.0)
        f = QFont(qp.font())
        f.setPixelSize(int(clamp(H * 0.10, 10, 200)))
        f.setBold(True)
        qp.setFont(f)
        qp.setOpacity(ta)
        tr = QRectF(0, H * 0.02 - (1 - ta) * H * 0.05, W, title_h - H * 0.02)
        qp.setPen(QColor(0, 0, 0, 120))
        qp.drawText(tr.translated(2 * ui, 2 * ui), Qt.AlignCenter, "¡CAMPEÓN!")
        qp.setPen(QColor("#FFD84D"))
        qp.drawText(tr, Qt.AlignCenter, "¡CAMPEÓN!")

        na = clamp((t - 0.9) / 0.5, 0.0, 1.0)
        f2 = QFont(f)
        f2.setPixelSize(int(clamp(H * 0.075, 9, 140)))
        qp.setFont(f2)
        name = QFontMetrics(f2).elidedText(champ.name or "Campeón", Qt.ElideRight, int(W * 0.9))
        qp.setOpacity(na)
        qp.setPen(QColor("white"))
        qp.drawText(QRectF(0, H - name_h, W, name_h * 0.9), Qt.AlignCenter, name)
        qp.setOpacity(1.0)

        # fuegos artificiales
        if anim:
            qp.setCompositionMode(QPainter.CompositionMode_Plus)
            qp.setPen(Qt.NoPen)
            qp.setBrush(QColor(255, 230, 170))
            for r in self.rockets:
                qp.drawEllipse(QPointF(r.x, r.y), 2.5 * ui + 1, 2.5 * ui + 1)
            for s in self.sparks:
                col = QColor(s.color)
                col.setAlpha(int(255 * min(1.0, 1.6 * s.life / s.max)))
                qp.setPen(QPen(col, max(1.0, s.size * ui), Qt.SolidLine, Qt.RoundCap))
                qp.drawLine(QPointF(s.px, s.py), QPointF(s.x, s.y))
            qp.setCompositionMode(QPainter.CompositionMode_SourceOver)

    # ---------------- ratón: clic repite, arrastrar mueve la vista ----------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press = e.position().toPoint()
            self._press_g = e.globalPosition().toPoint()
            self._panning = False
        else:
            e.ignore()

    def mouseMoveEvent(self, e):
        if self._panning:
            self.canvas.pan_to(e.globalPosition().toPoint())
            return
        if self._press is None or not (e.buttons() & Qt.LeftButton):
            return
        if (e.position().toPoint() - self._press).manhattanLength() < QApplication.startDragDistance():
            return
        self._panning = True
        self._press = None
        self.canvas.start_pan(self._press_g)
        self.canvas.pan_to(e.globalPosition().toPoint())

    def mouseReleaseEvent(self, e):
        if self._panning:
            self._panning = False
            self.canvas.end_pan()
            return
        if e.button() == Qt.LeftButton and self._press is not None:
            self._press = None
            self.play()


# ----------------------------------------------------------------------------
# Combates por rondas: pestañas + animación VERSUS + ganador + confirmar
# ----------------------------------------------------------------------------
VS_TABS = [("R1 Izq", "Ronda 1 · Izquierda", "L", 0), ("R1 Der", "Ronda 1 · Derecha", "R", 0),
           ("R2 Izq", "Ronda 2 · Izquierda", "L", 1), ("R2 Der", "Ronda 2 · Derecha", "R", 1),
           ("Semi Izq", "Semifinal · Izquierda", "L", 2), ("Semi Der", "Semifinal · Derecha", "R", 2),
           ("Final", "Final", "F", 3)]


def vs_matches(tab):
    """Combates de una pestaña: lista de (casilla A, casilla B o None si pasa directo, destino)."""
    _, _, side, r = VS_TABS[tab]
    if side == "F":
        return [(("L", 3, 0), ("R", 3, 0), ("C", 0, 0))]
    out = []
    for i in range(0, ROUNDS[r], 2):
        b = (side, r, i + 1) if i + 1 < ROUNDS[r] else None
        out.append(((side, r, i), b, (side, r + 1, i // 2)))
    return out


def vs_order():
    """Orden de juego: Izquierda, Derecha, Izquierda, Derecha... ronda por ronda, y al final la Final."""
    order = []
    for r in range(3):
        for m in range(len(vs_matches(2 * r))):
            order.append((2 * r, m))
            order.append((2 * r + 1, m))
    order.append((6, 0))
    return order


def vs_info(state, tab, idx):
    """(pa, pb, pasa_directo, listo, ganador 0/1/None, a, b, destino)"""
    a, b, dst = vs_matches(tab)[idx]
    pa = state[a]
    pb = state[b] if b is not None else None
    bye = b is None
    ready = pa is not None and (bye or pb is not None)
    cur = state[dst]
    winner = None
    if ready and cur is not None:
        if cur is pa:
            winner = 0
        elif cur is pb:
            winner = 1
    return pa, pb, bye, ready, winner, a, b, dst


def vs_pending(state, tab, idx):
    """Siguiente combate listo y sin ganador, siguiendo el orden de juego (nunca el mismo combate)."""
    order = vs_order()
    pos = order.index((tab, idx)) if (tab, idx) in order else -1
    for k in range(1, len(order) + 1):
        t, i = order[(pos + k) % len(order)]
        if (t, i) == (tab, idx):
            continue
        x = vs_info(state, t, i)
        if x[3] and x[4] is None:
            return t, i
    return None


class VersusView(QWidget):
    """Muestra un combate: aparición de los combatientes, VS, y animación del ganador."""
    picked = Signal(int)
    winFinished = Signal()
    WIN_DUR = 2.6

    def __init__(self):
        super().__init__()
        self.a = self.b = None
        self.winner = None
        self.bye = False
        self.msg = ""
        self.mode = "match"
        self.carry = [False, False]
        self.delays = [0.0, 0.0]
        self.ready_t = 0.0
        self.T = 99.0
        self._last = 0.0
        self.rects = [None, None]
        self.hover = -1
        self.sparks = []
        self.bursts = []
        self._finished = False
        self.chroma = None           # color de fondo para clave cromática (OBS)
        self.transparent = False     # fondo transparente (combates)
        self.stream_mode = False     # True mientras se captura para OBS: sin pistas ni resaltado
        self.setMouseTracking(True)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)

    # ---------------- control ----------------
    def show_match(self, a, b, winner, msg="", bye=False, carry=(False, False)):
        self.a, self.b, self.winner, self.msg, self.bye = a, b, winner, msg, bye
        self.mode = "match"
        self.hover = -1
        self.sparks, self.bursts = [], []
        self._finished = False
        self.carry = list(carry)
        ca, cb = self.carry
        if bye:
            self.delays = [0.0, 0.0]
        elif ca and not cb:
            self.delays = [0.0, 0.9]          # el ganador anterior ya está; el nuevo aparece después
        elif cb and not ca:
            self.delays = [0.9, 0.0]
        else:
            self.delays = [0.0, 0.6]
        self.ready_t = max(self.delays) + 1.0
        if a is None or winner is not None:
            self.T = 99.0                      # estático
            self.timer.stop()
        else:
            self.T = 0.0
            self._last = time.perf_counter()
            self.timer.start()
        self.update()

    def play_win(self, side):
        self.winner = side
        self.mode = "win"
        self.T = 0.0
        self.sparks = []
        self.bursts = [0.25, 0.7, 1.15, 1.6]
        self._finished = False
        self._last = time.perf_counter()
        self.timer.start()
        self.update()

    def _burst(self, cx, cy):
        W, H = max(1.0, float(self.width())), max(1.0, float(self.height()))
        n = random.randint(50, 75)
        base = min(W, H) * random.uniform(0.35, 0.6)
        c1 = QColor(random.choice(FIREWORK_COLORS))
        c2 = QColor(random.choice(FIREWORK_COLORS))
        for k in range(n):
            a = 2 * math.pi * k / n + random.uniform(-0.05, 0.05)
            sp = base * random.uniform(0.3, 1.0)
            self.sparks.append(_spark(cx, cy, math.cos(a) * sp, math.sin(a) * sp,
                                      random.uniform(0.9, 1.5), c1 if k % 2 == 0 else c2,
                                      random.uniform(1.6, 3.0)))

    def _tick(self):
        now = time.perf_counter()
        dt = min(0.05, max(0.0, now - self._last))
        self._last = now
        self.T += dt
        if self.mode == "win":
            W, H = float(self.width()), float(self.height())
            while self.bursts and self.bursts[0] <= self.T:
                self.bursts.pop(0)
                self._burst(W * random.uniform(0.25, 0.75), H * random.uniform(0.18, 0.5))
            g = H * 0.5
            damp = 1 - 1.5 * dt
            for sp in self.sparks:
                sp.px, sp.py = sp.x, sp.y
                sp.vx *= damp
                sp.vy = sp.vy * damp + g * dt
                sp.x += sp.vx * dt
                sp.y += sp.vy * dt
                sp.life -= dt
            self.sparks = [sp for sp in self.sparks if sp.life > 0]
            if self.T > self.WIN_DUR and not self.bursts and not self._finished:
                self._finished = True
                self.timer.stop()
                self.update()
                self.winFinished.emit()
                return
        elif self.T > self.ready_t + 6:
            self.timer.stop()
        self.update()

    # ---------------- geometría ----------------
    def _geom(self):
        W, H = float(self.width()), float(self.height())
        cw = min(W * 0.38, H * 0.5 * RATIO)
        ch = cw / RATIO
        cy = H * 0.46 - ch / 2
        return W, H, cw, ch, cy

    def _target_rects(self):
        W, H, cw, ch, cy = self._geom()
        if self.bye:
            return [QRectF((W - cw) / 2, cy, cw, ch), None]
        gap = W * 0.12
        return [QRectF(W / 2 - gap / 2 - cw, cy, cw, ch), QRectF(W / 2 + gap / 2, cy, cw, ch)]

    # ---------------- pintura ----------------
    def _card(self, qp, part, r, op, gold, dim, flash, hover, ui, H):
        qp.save()
        qp.setOpacity(op)
        rad = clamp(18 * ui, 8, 40)
        path = QPainterPath()
        path.addRoundedRect(r, rad, rad)
        qp.setPen(Qt.NoPen)
        qp.setBrush(QColor(255, 200, 80, 70 if gold else 35))
        m = (14 if gold else 8) * ui
        qp.drawRoundedRect(r.adjusted(-m, -m, m, m), rad + 6, rad + 6)
        qp.save()
        qp.setClipPath(path)
        pm = get_thumb(part.media, 1600)
        if pm is not None:
            draw_cover(qp, pm, r, part.fx, part.fy, part.zoom)
        else:
            qp.fillPath(path, QColor("#FFE6D1"))
        if dim:
            qp.fillRect(r, QColor(60, 60, 60, 190))
        elif hover:
            qp.fillRect(r, QColor(255, 255, 255, 45))
        if flash > 0:
            qp.fillRect(r, QColor(255, 255, 255, int(200 * flash)))
        qp.restore()
        qp.setBrush(Qt.NoBrush)
        qp.setPen(QPen(QColor(GOLD) if gold else QColor(ORANGE), max(2.0, (7 if (hover or gold) else 3) * ui)))
        qp.drawPath(path)
        ns = int(clamp(H * 0.035, 11, 34))
        draw_pill(qp, r.center().x(), r.bottom() + 10 * ui, max(r.width(), 120), part.name or "—",
                  bold=True, fg=INK, h=ns * 1.6, size=ns)
        if part.detail:
            ds = max(9, int(ns * 0.75))
            draw_pill(qp, r.center().x(), r.bottom() + 10 * ui + ns * 1.8, max(r.width(), 120), part.detail,
                      fg="#666666", h=ds * 1.6, size=ds)
        qp.restore()

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform |
                          QPainter.RenderHint.TextAntialiasing)
        W, H, cw, ch, cy = self._geom()
        if self.transparent:
            pass                                   # sin fondo: se ve lo que haya detrás (o canal alfa en OBS)
        elif self.chroma is not None:
            qp.fillRect(self.rect(), QColor(self.chroma))
        else:
            g = QLinearGradient(0, 0, 0, H)
            g.setColorAt(0.0, QColor("#150E2B"))
            g.setColorAt(0.65, QColor("#2A1226"))
            g.setColorAt(1.0, QColor("#40190A"))
            qp.fillRect(self.rect(), g)
        self.rects = [None, None]
        if self.a is None:
            if self.stream_mode:
                return
            f = QFont(qp.font())
            f.setPixelSize(int(clamp(H * 0.045, 14, 40)))
            f.setBold(True)
            qp.setFont(f)
            qp.setPen(QColor(255, 255, 255, 200))
            qp.drawText(QRectF(0, 0, W, H), Qt.AlignCenter | Qt.TextWordWrap, self.msg)
            return
        ui = clamp(H / 880.0, 0.4, 2.0)
        t = self.T
        win_mode = self.mode == "win"
        targets = self._target_rects()
        parts = [self.a, self.b]
        clickable = (not win_mode) and self.winner is None and t >= self.ready_t
        for i in range(2):
            tr, part = targets[i], parts[i]
            if tr is None or part is None:
                continue
            s, op, flash, dim, gold = 1.0, 1.0, 0.0, False, False
            center = tr.center()
            if win_mode:
                if i == self.winner:
                    p = ease_out_back(t / 0.8)
                    k = clamp(t / 0.6, 0.0, 1.0)
                    center = QPointF(tr.center().x() + (W / 2 - tr.center().x()) * k, tr.center().y())
                    s = 1 + 0.3 * p
                    gold = True
                else:
                    k = clamp(t / 0.5, 0.0, 1.0)
                    op = 1 - k
                    center = QPointF(tr.center().x() + (-1 if i == 0 else 1) * cw * 0.3 * k, tr.center().y())
                    if op <= 0:
                        continue
            elif self.winner is not None:
                gold = i == self.winner
                dim = (not gold) and not self.bye
            elif not self.carry[i]:
                lt = t - self.delays[i]
                if lt < 0:
                    continue
                s = 0.45 + 0.55 * ease_out_back(lt / 0.5)
                op = clamp(lt / 0.3, 0.0, 1.0)
                flash = clamp(1 - lt / 0.55, 0.0, 1.0)
            r = QRectF(0, 0, tr.width() * s, tr.height() * s)
            r.moveCenter(center)
            if clickable and flash == 0.0:
                self.rects[i] = QRectF(tr)
            self._card(qp, part, r, op, gold, dim, flash, clickable and self.hover == i and not self.stream_mode, ui, H)

        if not self.bye:                                        # VS
            if win_mode:
                va = 1 - clamp(t / 0.3, 0.0, 1.0)
                vs = 1.0
            else:
                va = 1.0
                vs = 1.0 if self.winner is not None else ease_out_back((t - (max(self.delays) + 0.35)) / 0.45)
            if vs > 0 and va > 0:
                pulse = 1.0 + (0.05 * math.sin(t * 6) if (not win_mode and self.winner is None) else 0.0)
                f = QFont(qp.font())
                f.setPixelSize(max(10, int(H * 0.16 * vs * pulse)))
                f.setBold(True)
                f.setItalic(True)
                qp.setFont(f)
                qp.setOpacity(va)
                rc = QRectF(W / 2 - W * 0.12, cy, W * 0.24, ch)
                qp.setPen(QColor(0, 0, 0, 140))
                qp.drawText(rc.translated(3 * ui, 3 * ui), Qt.AlignCenter, "VS")
                qp.setPen(QColor("#FFD84D"))
                qp.drawText(rc, Qt.AlignCenter, "VS")
                qp.setOpacity(1.0)

        if win_mode or self.winner is not None:                 # título GANADOR
            ta = clamp((t - 0.35) / 0.4, 0.0, 1.0) if win_mode else 1.0
            f = QFont(qp.font())
            f.setPixelSize(int(clamp(H * 0.07, 14, 120)))
            f.setBold(True)
            f.setItalic(False)
            qp.setFont(f)
            qp.setOpacity(ta)
            tr_ = QRectF(0, H * 0.015 - (1 - ta) * H * 0.04, W, H * 0.11)
            qp.setPen(QColor(0, 0, 0, 130))
            qp.drawText(tr_.translated(2 * ui, 2 * ui), Qt.AlignCenter, "¡GANADOR!")
            qp.setPen(QColor("#FFD84D"))
            qp.drawText(tr_, Qt.AlignCenter, "¡GANADOR!")
            qp.setOpacity(1.0)
        elif clickable and not self.stream_mode:
            f = QFont(qp.font())
            f.setPixelSize(int(clamp(H * 0.026, 11, 24)))
            f.setBold(False)
            f.setItalic(False)
            qp.setFont(f)
            qp.setPen(QColor(255, 255, 255, 180))
            hint = "Pasa directo a la siguiente ronda. Toca la miniatura para confirmar." if self.bye \
                else "Toca la miniatura del ganador"
            qp.drawText(QRectF(0, H * 0.86, W, H * 0.06), Qt.AlignCenter, hint)

        if self.sparks:                                         # fuegos artificiales
            qp.setCompositionMode(QPainter.CompositionMode_Plus)
            for sp in self.sparks:
                col = QColor(sp.color)
                col.setAlpha(int(255 * min(1.0, 1.6 * sp.life / sp.max)))
                qp.setPen(QPen(col, max(1.0, sp.size * ui), Qt.SolidLine, Qt.RoundCap))
                qp.drawLine(QPointF(sp.px, sp.py), QPointF(sp.x, sp.y))
            qp.setCompositionMode(QPainter.CompositionMode_SourceOver)

    # ---------------- ratón ----------------
    def _hit(self, pos):
        for i, r in enumerate(self.rects):
            if r is not None and r.contains(pos):
                return i
        return -1

    def mouseMoveEvent(self, e):
        h = self._hit(e.position())
        if h != self.hover:
            self.hover = h
            self.setCursor(Qt.PointingHandCursor if h >= 0 else Qt.ArrowCursor)
            self.update()

    def leaveEvent(self, e):
        self.hover = -1
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            h = self._hit(e.position())
            if h >= 0:
                self.picked.emit(h)


class VersusOverlay(QWidget):
    """Pantalla con pestañas por ronda (Izq/Der) para elegir ganadores combate a combate."""
    closed = Signal()
    TABS = VS_TABS

    def __init__(self, page):
        super().__init__(page)
        self.page = page
        self.canvas = page.canvas
        self.tab = 0
        self.idx = 0
        self.busy = False
        self.chroma = None
        self.transparent_opt = False
        self.cur = None                      # combate que se está resolviendo
        self.carry = {"L": None, "R": None, "F": None}
        self.setFocusPolicy(Qt.StrongFocus)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 18, 80, 18)
        lay.setSpacing(10)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.btns = []
        for n, (short, full, side, r) in enumerate(self.TABS):
            b = QPushButton(short)
            b.setObjectName("soft")
            b.setCheckable(True)
            b.setToolTip(full)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("QPushButton { padding:6px 14px; font-size:13px; }")
            b.clicked.connect(lambda _=False, n=n: self.select_tab(n))
            self.group.addButton(b)
            self.btns.append(b)
            row.addWidget(b)
        row.addStretch()
        lay.addLayout(row)
        self.view = VersusView()
        self.view.picked.connect(self.on_pick)
        self.view.winFinished.connect(self.after_win)
        lay.addWidget(self.view, 1)
        nav = QHBoxLayout()
        self.b_prev = QPushButton("◀ Anterior")
        self.b_next = QPushButton("Siguiente ▶")
        for b in (self.b_prev, self.b_next):
            b.setObjectName("soft")
            b.setCursor(Qt.PointingHandCursor)
        self.lbl = QLabel("")
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet("color:white; font-size:16px; font-weight:600; background:transparent;")
        nav.addWidget(self.b_prev)
        nav.addWidget(self.lbl, 1)
        nav.addWidget(self.b_next)
        lay.addLayout(nav)
        self.b_prev.clicked.connect(lambda: self.go(-1))
        self.b_next.clicked.connect(lambda: self.go(1))
        self.btn_close = QPushButton("×", self)
        self.btn_close.setFixedSize(46, 46)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setToolTip("Cerrar (Esc)")
        self.btn_close.setStyleSheet(
            "QPushButton { background:rgba(255,255,255,235); color:#E8590C; border:none; "
            "border-radius:23px; font-size:30px; font-weight:600; padding-bottom:3px; }"
            "QPushButton:hover { background:white; }")
        self.btn_close.clicked.connect(self.close_overlay)
        self.hide()

    def set_busy(self, on):
        self.busy = on
        for b in self.btns:
            b.setEnabled(not on)
        if on:
            self.b_prev.setEnabled(False)
            self.b_next.setEnabled(False)

    # ----- ciclo de vida -----
    def open(self):
        self.carry = {"L": None, "R": None, "F": None}
        self.set_busy(False)
        self.set_chroma(self.canvas.chroma)
        self.set_clean(self.page.obs_mode)
        self.relayout()
        self.show()
        self.raise_()
        self.setFocus()
        first = None
        for t, i in vs_order():
            x = vs_info(self.canvas.state, t, i)
            if x[3] and x[4] is None:
                first = (t, i)
                break
        self.tab, self.idx = first if first else (0, 0)
        self.btns[self.tab].setChecked(True)
        self.show_current()

    def close_overlay(self):
        if self.isVisible():
            self.view.timer.stop()
            self.set_busy(False)
            self.hide()
            self.closed.emit()

    def relayout(self):
        p = self.parentWidget()
        self.setGeometry(0, 0, p.width(), p.height())
        self.btn_close.move(self.width() - 46 - 18, 18)
        self.btn_close.raise_()

    def set_chroma(self, color):
        self.chroma = color
        self.view.chroma = color
        self._apply_bg()

    def set_transparent(self, on):
        self.transparent_opt = bool(on)
        self._apply_bg()

    def _apply_bg(self):
        # el croma, si está elegido, manda sobre la transparencia
        self.view.transparent = self.transparent_opt and self.chroma is None
        self.view.update()
        self.update()

    def set_clean(self, on):
        """Modo OBS: oculta pestañas, botones y márgenes; queda solo el combate."""
        for w in (*self.btns, self.b_prev, self.b_next, self.lbl, self.btn_close):
            w.setVisible(not on)
        self.layout().setContentsMargins(0, 0, 0, 0) if on else self.layout().setContentsMargins(24, 18, 80, 18)
        self.view.stream_mode = False

    def paintEvent(self, e):
        qp = QPainter(self)
        if self.view.transparent:                  # tablero gris: indica que el fondo es transparente
            qp.fillRect(self.rect(), QColor("#3A3A3A"))
            qp.setPen(Qt.NoPen)
            qp.setBrush(QColor("#2E2E2E"))
            sq = 24
            for y in range(0, self.height(), sq):
                for x in range(0, self.width(), sq):
                    if ((x // sq) + (y // sq)) % 2 == 0:
                        qp.drawRect(x, y, sq, sq)
        else:
            qp.fillRect(self.rect(), QColor(self.chroma) if self.chroma else QColor("#150E2B"))

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close_overlay()
        elif e.key() == Qt.Key_Left:
            self.go(-1)
        elif e.key() == Qt.Key_Right:
            self.go(1)
        else:
            super().keyPressEvent(e)

    # ----- navegación -----
    def select_tab(self, n):
        if self.busy:
            return
        self.tab = n
        self.btns[n].setChecked(True)
        self.idx = 0
        for i in range(len(vs_matches(n))):
            x = vs_info(self.canvas.state, n, i)
            if x[3] and x[4] is None:
                self.idx = i
                break
        self.show_current()

    def go(self, d):
        if self.busy:
            return
        self.idx = clamp(self.idx + d, 0, len(vs_matches(self.tab)) - 1)
        self.show_current()

    def show_current(self):
        pa, pb, bye, ready, winner, a, b, dst = vs_info(self.canvas.state, self.tab, self.idx)
        total = len(vs_matches(self.tab))
        if not ready:
            self.view.show_match(None, None, None, "Faltan participantes en este combate.\n"
                                 "Completa los combates anteriores o llena las casillas.")
        else:
            key = self.TABS[self.tab][2]
            c = self.carry.get(key)
            carry = (c is not None and pa is c, c is not None and pb is c)
            self.view.show_match(pa, pb, winner, "", bye, carry)
        self.lbl.setText(f"{self.TABS[self.tab][1]}  ·  Combate {self.idx + 1} de {total}")
        self.b_prev.setEnabled(self.idx > 0)
        self.b_next.setEnabled(self.idx < total - 1)

    # ----- elegir ganador -----
    def on_pick(self, side):
        if self.busy:
            return
        pa, pb, bye, ready, winner, a, b, dst = vs_info(self.canvas.state, self.tab, self.idx)
        if not ready or winner is not None:
            return
        src = a if side == 0 else b
        part = pa if side == 0 else pb
        name = part.name or "este participante"
        box = QMessageBox(self)
        box.setWindowTitle("Confirmar ganador")
        if bye:
            box.setText(f"¿Confirmar que «{name}» pasa a la siguiente ronda?")
        else:
            box.setText(f"¿Declarar a «{name}» ganador de este combate?")
            box.setInformativeText("El rival quedará marcado como eliminado.")
        yes = box.addButton("Confirmar", QMessageBox.AcceptRole)
        box.addButton("Cancelar", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is not yes:
            return
        self.set_busy(True)
        self.cur = (self.tab, self.idx, dst)
        self.carry[self.TABS[self.tab][2]] = part
        self.canvas.perform_drop(src, dst)
        self.view.play_win(side)               # animación de ganador; al terminar sigue after_win

    def after_win(self):
        if self.cur is None:
            return
        tab, idx, dst = self.cur
        self.cur = None
        self.set_busy(False)
        if dst[0] == "C":                      # terminó el torneo: cinemática del campeón
            self.close_overlay()
            self.canvas.stage.play()
            return
        nxt = vs_pending(self.canvas.state, tab, idx)
        if nxt is None:
            self.tab, self.idx = tab, idx
        else:
            self.tab, self.idx = nxt
        self.btns[self.tab].setChecked(True)
        self.show_current()


class BracketCanvas(QWidget):
    changed = Signal()
    previewRequested = Signal(object, bool)

    def __init__(self):
        super().__init__()
        self.zoom = 1.0
        self.scroll_area = None
        self._pan = None
        self.chroma = None        # color de fondo para clave cromática (OBS), o None
        self.transparent_opt = False   # fondo transparente (la parte dibujada no cambia)
        self.stream_mode = False       # True mientras se captura para OBS (sin tablero de ajedrez)
        self.setCursor(Qt.OpenHandCursor)
        self.setAcceptDrops(True)
        self.setMinimumSize(DESIGN_W, DESIGN_H)
        self.ui = 1.0
        self.eliminated = set()   # casillas cuyo participante perdió su enfrentamiento
        self.state = {}
        self.widgets = {}
        for side in "LR":
            for r, n in enumerate(ROUNDS):
                for i in range(n):
                    self._add_slot((side, r, i))
        self._add_slot(("C", 0, 0))
        self.geo = {}
        self.layout_info = {}

        self.bg_path = ""
        self.bg_blur = 12
        self.bg_veil = 35
        self._bg_loaded = None
        self._bg_src = None
        self._bg_pm = None

        # título editable
        self.title = QLineEdit("Mi Torneo", self)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setPlaceholderText("Título del torneo")
        self.title.setStyleSheet(
            f"QLineEdit {{ background:rgba(255,255,255,190); border:2px solid transparent; "
            f"border-radius:30px; font-weight:800; color:{ORANGE_D}; }}"
            f"QLineEdit:focus {{ border-color:{ORANGE}; background:rgba(255,255,255,235); }}")
        self.title.textEdited.connect(lambda _: self.changed.emit())

        # cinemática del campeón
        self.stage = ChampionStage(self)

    @property
    def transparent(self):
        return self.transparent_opt and self.chroma is None

    def grab_alpha(self):
        """Imagen del cuadro con canal alfa: fondo transparente, dibujos intactos."""
        self.stream_mode = True
        try:
            img = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
            img.fill(0)
            self.render(img, QPoint(), QRegion(), QWidget.RenderFlag.DrawChildren)
        finally:
            self.stream_mode = False
        return img

    def set_zoom(self, z):
        self.zoom = z
        self.setMinimumSize(int(DESIGN_W * z), int(DESIGN_H * z))
        self.updateGeometry()

    def minimumSizeHint(self):
        return QSize(int(DESIGN_W * self.zoom), int(DESIGN_H * self.zoom))

    def autoscroll(self, gpos):
        if self.scroll_area is not None:
            self.scroll_area.autoscroll(gpos)

    # ---------------- mover la vista arrastrando con el mouse ----------------
    def start_pan(self, gpos):
        sa = self.scroll_area
        if sa is None or self._pan is not None:
            return
        self._pan = (gpos, sa.horizontalScrollBar().value(), sa.verticalScrollBar().value())
        QApplication.setOverrideCursor(Qt.ClosedHandCursor)

    def pan_to(self, gpos):
        if self._pan is None or self.scroll_area is None:
            return
        p0, h0, v0 = self._pan
        self.scroll_area.horizontalScrollBar().setValue(h0 - (gpos.x() - p0.x()))
        self.scroll_area.verticalScrollBar().setValue(v0 - (gpos.y() - p0.y()))

    def end_pan(self):
        if self._pan is not None:
            self._pan = None
            QApplication.restoreOverrideCursor()

    def mousePressEvent(self, e):
        if e.button() in (Qt.LeftButton, Qt.MiddleButton):
            self.start_pan(e.globalPosition().toPoint())
            e.accept()
        else:
            super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._pan is not None:
            self.pan_to(e.globalPosition().toPoint())

    def mouseReleaseEvent(self, e):
        self.end_pan()

    def _add_slot(self, key):
        self.state[key] = None
        self.widgets[key] = SlotWidget(self, key)

    # ---------------- reglas ----------------
    def is_alone(self, key):
        side, r, i = key
        if side == "C" or self.state[key] is None:
            return False
        if r == 3:
            other = ("R" if side == "L" else "L", 3, 0)
            return self.state[other] is None
        j = i ^ 1
        if j >= ROUNDS[r]:
            return True            # casilla sin pareja: pasa directo
        return self.state[(side, r, j)] is None

    def drop_kind(self, src, dst):
        if src == dst or self.state.get(src) is None or src[0] == "C":
            return None
        if dst[0] == "C":
            return "advance" if src[1] == 3 else None
        if src[1] == dst[1]:
            return "swap"
        if dst[0] == src[0] and dst[1] == src[1] + 1 and dst[2] == src[2] // 2:
            return "advance"
        return None

    def rival_of(self, key):
        side, r, i = key
        if r == 3:
            return ("R" if side == "L" else "L", 3, 0)
        j = i ^ 1
        return (side, r, j) if j < ROUNDS[r] else None

    def slot_status(self, key):
        """'elim' = perdió su enfrentamiento, 'alone' = sin rival, None = normal."""
        if self.state.get(key) is None:
            return None
        if key in self.eliminated:
            return "elim"
        return "alone" if self.is_alone(key) else None

    def toggle_eliminated(self, key):
        if key in self.eliminated:
            self.eliminated.discard(key)
        elif self.state.get(key) is not None:
            self.eliminated.add(key)
        self.refresh()
        self.changed.emit()

    def perform_drop(self, src, dst):
        kind = self.drop_kind(src, dst)
        if kind == "swap":
            es, ed = src in self.eliminated, dst in self.eliminated
            self.eliminated.discard(src)
            self.eliminated.discard(dst)
            self.state[src], self.state[dst] = self.state[dst], self.state[src]
            if es:
                self.eliminated.add(dst)
            if ed:
                self.eliminated.add(src)
        elif kind == "advance":
            self.state[dst] = self.state[src]
            self.eliminated.discard(src)
            self.eliminated.discard(dst)
            loser = self.rival_of(src)                 # el rival del que avanza se pone gris
            if loser is not None and self.state.get(loser) is not None:
                self.eliminated.add(loser)
        else:
            return
        self.refresh()
        if kind == "advance" and dst[0] == "C":
            self.stage.play()
        self.changed.emit()

    # ---------------- acciones ----------------
    def refresh(self):
        for w in self.widgets.values():
            w.update()
        self.stage.sync()
        self.update()

    def pick_file(self, key):
        paths, _ = QFileDialog.getOpenFileNames(self, "Selecciona imágenes o videos", "", FILE_FILTER)
        if not paths:
            return
        if len(paths) == 1:
            self.assign_file(key, paths[0])
        else:
            self.import_many(paths)

    def assign_file(self, key, path):
        ext = Path(path).suffix.lower()
        if key[0] == "C" or (ext not in IMG_EXT and ext not in VID_EXT):
            return
        try:
            media = import_media(path)
        except Exception as ex:
            QMessageBox.warning(self, "Error", f"No se pudo cargar el archivo:\n{ex}")
            return
        part = self.state[key]
        if part is None:
            part = Participant(name=Path(path).stem[:40], media=media)
            self.state[key] = part
        else:
            part.media = media
            part.fx, part.fy, part.zoom = 0.5, 0.5, 1.0
        self.refresh()
        self.changed.emit()

    def import_many(self, paths=None):
        """Reparte varios archivos, en orden, por las casillas libres de la primera ronda."""
        if paths is None:
            paths, _ = QFileDialog.getOpenFileNames(self, "Selecciona varias imágenes o videos", "", FILE_FILTER)
        paths = sorted((p for p in paths if Path(p).suffix.lower() in (IMG_EXT | VID_EXT)), key=natural_key)
        if not paths:
            return
        order = [("L", 0, i) for i in range(6)] + [("R", 0, i) for i in range(6)]
        free = [k for k in order if self.state[k] is None]
        placed = 0
        for key, p in zip(free, paths):
            try:
                media = import_media(p)
            except Exception:
                continue
            self.state[key] = Participant(name=Path(p).stem[:40], media=media)
            placed += 1
        self.refresh()
        if placed:
            self.changed.emit()
        if placed < len(paths):
            QMessageBox.information(
                self, "Casillas llenas",
                f"Se colocaron {placed} de {len(paths)} archivos: no quedan más casillas libres "
                f"en la primera ronda.")

    def open_preview(self, key, crop=False):
        if self.state[key] is not None:
            self.previewRequested.emit(key, crop)

    def reset(self):
        self.eliminated.clear()
        for k in self.state:
            self.state[k] = None
        self.title.setText("Mi Torneo")
        self.set_background("", 12, 35)
        self.refresh()

    # ---------------- fondo ----------------
    def set_background(self, path, blur, veil):
        self.bg_path, self.bg_blur, self.bg_veil = path, int(blur), int(veil)
        if path != self._bg_loaded:
            self._bg_loaded = path
            self._bg_src = None
            if path and os.path.exists(path):
                pm = QPixmap(path)
                if not pm.isNull():
                    if pm.width() > 1280:
                        pm = pm.scaledToWidth(1280, Qt.SmoothTransformation)
                    self._bg_src = pm
        self._bg_pm = blur_pixmap(self._bg_src, self.bg_blur) if self._bg_src else None
        self.update()

    # ---------------- guardar / cargar (.trn = zip con project.json + media) ----------------
    def save_to(self, path):
        parts, idx, media_names = [], {}, {}

        def mname(p):
            if not p or not os.path.exists(p):
                return None
            if p not in media_names:
                media_names[p] = f"media/{len(media_names)}{Path(p).suffix.lower()}"
            return media_names[p]

        slots = {}
        for key, p in self.state.items():
            if p is None:
                continue
            if id(p) not in idx:
                idx[id(p)] = len(parts)
                parts.append({"name": p.name, "detail": p.detail, "media": mname(p.media),
                              "fx": p.fx, "fy": p.fy, "zoom": p.zoom})
            slots[":".join(str(x) for x in key)] = idx[id(p)]
        data = {
            "app": "TournamentMaker", "version": 1, "title": self.title.text(),
            "background": {"media": mname(self.bg_path), "blur": self.bg_blur, "veil": self.bg_veil},
            "participants": parts, "slots": slots,
            "eliminated": [":".join(str(x) for x in k) for k in sorted(self.eliminated)
                           if self.state.get(k) is not None],
        }
        tmp_out = path + ".tmp"
        with zipfile.ZipFile(tmp_out, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("project.json", json.dumps(data, ensure_ascii=False, indent=1))
            for src, name in media_names.items():
                z.write(src, name)
        os.replace(tmp_out, path)

    def load_from(self, path):
        with zipfile.ZipFile(path) as z:
            data = json.loads(z.read("project.json").decode("utf-8"))
            cache = {}

            def extract(name):
                if not name:
                    return ""
                if name not in cache:
                    dest = os.path.join(TMP, uuid.uuid4().hex + Path(name).suffix.lower())
                    with z.open(name) as f, open(dest, "wb") as o:
                        shutil.copyfileobj(f, o)
                    cache[name] = dest
                return cache[name]

            parts = [Participant(d.get("name", ""), d.get("detail", ""), extract(d.get("media")),
                                 float(d.get("fx", 0.5)), float(d.get("fy", 0.5)), float(d.get("zoom", 1.0)))
                     for d in data.get("participants", [])]
            bg = data.get("background", {})
            bg_path = extract(bg.get("media"))
        for k in self.state:
            self.state[k] = None
        for k, v in data.get("slots", {}).items():
            s, r, i = k.split(":")
            key = (s, int(r), int(i))
            if key in self.state and 0 <= v < len(parts):
                self.state[key] = parts[v]
        self.eliminated = set()
        for k in data.get("eliminated", []):
            s, r, i = k.split(":")
            if (s, int(r), int(i)) in self.state:
                self.eliminated.add((s, int(r), int(i)))
        self.title.setText(data.get("title", "Mi Torneo"))
        self.set_background(bg_path, bg.get("blur", 12), bg.get("veil", 35))
        self.refresh()

    # ---------------- captura de pantalla ----------------
    def take_screenshot(self):
        self.title.clearFocus()
        QApplication.processEvents()
        pm = QPixmap.fromImage(self.grab_alpha()) if self.transparent else self.grab()   # cuadro completo
        QApplication.clipboard().setPixmap(pm)           # también queda copiada al portapapeles
        name = re.sub(r'[\\/:*?"<>|]+', "_", self.title.text().strip() or "torneo")
        path, _ = QFileDialog.getSaveFileName(self, "Guardar captura", name + ".png",
                                              "PNG (*.png);;JPG (*.jpg);;WEBP (*.webp)")
        if not path:
            return
        if not Path(path).suffix:
            path += ".png"
        if not pm.save(path):
            QMessageBox.warning(self, "Error", "No se pudo guardar la captura.")

    # ---------------- arrastrar archivos sobre el fondo ----------------
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() or e.mimeData().hasFormat(MIME):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        self.autoscroll(self.mapToGlobal(e.position().toPoint()))
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            self.import_many([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()])
            e.acceptProposedAction()

    # ---------------- geometría (se adapta a cualquier tamaño) ----------------
    def resizeEvent(self, e):
        W, H = max(1, self.width()), max(1, self.height())
        ui = clamp(min(W / float(DESIGN_W), H / float(DESIGN_H)), 0.3, 3.0)
        self.ui = ui
        margin = int(28 * ui)
        th = int(clamp(58 * ui, 30, 200))
        ty = int(clamp(14 * ui, 6, 60))
        lab_h = int(clamp(22 * ui, 14, 70))
        top = ty + th + int(10 * ui) + lab_h + int(10 * ui)
        bottom = H - int(20 * ui)
        avail = max(60, bottom - top)
        nh, dh, gp = text_heights(ui)
        over = nh + dh + 2 * gp
        vgap = max(4, int(8 * ui))
        hgap_min = max(8, int(24 * ui))
        sw_h = (W - 2 * margin - 8 * hgap_min) / 9.0
        sh_v = ((avail - 5 * vgap) / 6.0) - over
        sw = max(24.0, min(sw_h, sh_v * RATIO))
        sh = sw / RATIO
        gap = max(4.0, (W - 2 * margin - 9 * sw) / 8.0)
        cs = bracket_centers(top, bottom)
        geo = {}
        for side in "LR":
            for r, n in enumerate(ROUNDS):
                col = r if side == "L" else 8 - r
                x = margin + col * (sw + gap)
                for i in range(n):
                    cy = cs[(r, i)]
                    geo[(side, r, i)] = QRectF(x, cy - (sh + over) / 2, sw, sh + over)
        cw = sw * 1.3
        chh = cw / RATIO + over
        cx = margin + 4 * (sw + gap) + sw / 2
        cyc = cs[(3, 0)]
        geo[("C", 0, 0)] = QRectF(cx - cw / 2, cyc - chh / 2, cw, chh)
        self.geo = geo
        self.layout_info = {"top": top, "sw": sw, "gap": gap, "margin": margin, "lab_h": lab_h}
        for k, rect in geo.items():
            w = self.widgets[k]
            w.k = ui
            w.setGeometry(rect.toRect())
            w.update()

        # cinemática del campeón: entre las dos columnas de finalistas, sobre la casilla Campeón
        cgeo = geo[("C", 0, 0)]
        label_h = max(18, int(28 * ui))
        s_bottom = cgeo.top() - label_h - int(18 * ui)
        s_left, s_right = geo[("L", 3, 0)].left(), geo[("R", 3, 0)].right()
        self.stage.setGeometry(QRectF(s_left, top, s_right - s_left, max(40.0, s_bottom - top)).toRect())

        # título
        tw = int(min(W * 0.46, 760 * ui))
        self.title.setFixedSize(tw, th)
        self.title.move((W - tw) // 2, ty)
        f = self.title.font()
        f.setPixelSize(int(clamp(36 * ui, 12, 120)))
        self.title.setFont(f)
        super().resizeEvent(e)

    # ---------------- pintura de fondo, líneas y etiquetas ----------------
    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform |
                          QPainter.RenderHint.TextAntialiasing)
        r = QRectF(self.rect())
        if self.transparent:
            if not self.stream_mode:          # en la ventana: tablero gris = transparente
                qp.fillRect(r, QColor("#3A3A3A"))
                qp.setPen(Qt.NoPen)
                qp.setBrush(QColor("#2E2E2E"))
                sq = 24
                for y in range(0, self.height(), sq):
                    for x in range(0, self.width(), sq):
                        if ((x // sq) + (y // sq)) % 2 == 0:
                            qp.drawRect(x, y, sq, sq)
        elif self.chroma is not None:
            qp.fillRect(r, QColor(self.chroma))
        elif self._bg_pm is not None:
            draw_cover(qp, self._bg_pm, r)
            qp.fillRect(r, QColor(255, 255, 255, int(self.bg_veil * 2.55)))
        else:
            g = QLinearGradient(0, 0, r.width(), r.height())
            g.setColorAt(0.0, QColor("#FFFFFF"))
            g.setColorAt(1.0, QColor("#FFE6CF"))
            qp.fillRect(r, g)
        if not self.geo:
            return
        ui = self.ui
        for under in (True, False):
            pen = QPen(QColor(255, 255, 255, 170) if under else QColor(ORANGE),
                       max(2.5, 7 * ui) if under else max(1.5, 3 * ui),
                       Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            qp.setPen(pen)
            for a, b in bracket_links():
                elbow(qp, self.geo[a], self.geo[b])
        lab_h = self.layout_info["lab_h"]
        y = self.layout_info["top"] - int(10 * ui) - lab_h
        pitch = self.layout_info["sw"] + self.layout_info["gap"]
        for side in "LR":
            for rr in range(4):
                rect = self.geo[(side, rr, 0)]
                draw_pill(qp, rect.center().x(), y, max(pitch - 4, rect.width()), ROUND_NAMES[rr],
                          bold=True, fg=ORANGE_D, alpha=205, h=lab_h, size=max(8, int(13 * ui)))
        c = self.geo[("C", 0, 0)]
        ch = max(18, int(28 * ui))
        draw_pill(qp, c.center().x(), c.top() - ch - int(8 * ui), max(c.width(), int(110 * ui)),
                  "CAMPEÓN", bold=True, fg="#8A6100", alpha=235, h=ch, size=max(9, int(15 * ui)))


# ----------------------------------------------------------------------------
# Servidor para la fuente "Navegador" de OBS (no depende de detectar la ventana)
# ----------------------------------------------------------------------------
def obs_log(msg):
    """Escribe en la consola (cmd). Si no hay consola o no admite el texto, se ignora."""
    try:
        print(msg, flush=True)
    except Exception:
        pass


OBS_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Tournament Maker</title>
<style>html,body{margin:0;height:100%;background:transparent;overflow:hidden}
img{width:100%;height:100%;object-fit:contain;display:block}</style></head>
<body><img id="v" src="/stream">
<script>var v=document.getElementById('v');
v.onerror=function(){setTimeout(function(){v.src='/stream?'+Date.now();},1000);};</script>
</body></html>"""


class _ObsHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        owner = self.server.owner
        if path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", OBS_PAGE.encode("utf-8"))
        elif path == "/frame.jpg":
            frame = owner._frame
            if frame is None:
                self._send(503, "text/plain", b"sin imagen todavia")
            else:
                self._send(200, owner._ctype, frame)
        elif path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            owner._clients += 1
            last = -1
            try:
                while not owner._stopped:
                    with owner._cv:
                        owner._cv.wait_for(lambda: owner._seq != last or owner._stopped, timeout=1.0)
                        frame, seq, ctype = owner._frame, owner._seq, owner._ctype
                    if owner._stopped:
                        break
                    if frame is None or seq == last:
                        continue
                    last = seq
                    self.wfile.write(b"--frame\r\nContent-Type: %s\r\nContent-Length: %d\r\n\r\n" % (ctype.encode(), len(frame)))
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()
            except OSError:
                pass
            finally:
                owner._clients -= 1
        else:
            self._send(404, "text/plain", b"no encontrado")


class _Httpd(ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True


class MjpegServer:
    """Sirve el cuadro como video MJPEG en http://localhost:PUERTO (solo este equipo)."""

    def __init__(self, base_port=8765):
        self.base_port = base_port
        self.port = None
        self._httpd = None
        self._frame = None
        self._ctype = "image/jpeg"
        self._seq = 0
        self._clients = 0
        self._stopped = False
        self._cv = threading.Condition()

    @property
    def url(self):
        return f"http://localhost:{self.port}"

    @property
    def clients(self):
        return self._clients

    def start(self):
        last_err = None
        for p in range(self.base_port, self.base_port + 10):
            try:
                self._httpd = _Httpd(("127.0.0.1", p), _ObsHandler)
                self.port = p
                break
            except OSError as ex:
                last_err = ex
        if self._httpd is None:
            raise OSError(f"No hay puertos libres ({last_err})")
        self._httpd.owner = self
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()
        obs_log("")
        obs_log("-" * 62)
        obs_log(" Direccion para OBS  (Fuentes > + > Navegador):")
        obs_log("")
        obs_log(f"     {self.url}")
        obs_log("-" * 62)
        obs_log("")

    def push(self, jpg_bytes, ctype="image/jpeg"):
        with self._cv:
            self._frame = jpg_bytes
            self._ctype = ctype
            self._seq += 1
            self._cv.notify_all()

    def stop(self):
        self._stopped = True
        with self._cv:
            self._cv.notify_all()
        if self._httpd is not None:
            threading.Thread(target=self._httpd.shutdown, daemon=True).start()
            self._httpd.server_close()


class BoardScroll(QScrollArea):
    zoomRequested = Signal(int)

    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            self.zoomRequested.emit(1 if e.angleDelta().y() > 0 else -1)
            e.accept()
        else:
            super().wheelEvent(e)

    def autoscroll(self, gpos):
        """Desplaza el cuadro cuando se arrastra cerca del borde."""
        vp = self.viewport()
        p = vp.mapFromGlobal(gpos)
        edge, step = 70, 26
        hb, vb = self.horizontalScrollBar(), self.verticalScrollBar()
        if p.x() < edge:
            hb.setValue(hb.value() - step)
        elif p.x() > vp.width() - edge:
            hb.setValue(hb.value() + step)
        if p.y() < edge:
            vb.setValue(vb.value() - step)
        elif p.y() > vp.height() - edge:
            vb.setValue(vb.value() + step)


class TournamentPage(QWidget):
    """Cuadro con scroll y zoom + botones flotantes + vista previa superpuesta."""
    changed = Signal()
    backRequested = Signal()
    saveRequested = Signal()
    saveAsRequested = Signal()
    obsModeChanged = Signal(bool)
    windowSizeRequested = Signal(int, int)
    ZMIN, ZMAX = 0.3, 2.0

    def __init__(self):
        super().__init__()
        self.obs_mode = False
        self._prev_zoom = 1.0
        self.server = None
        self.srv_timer = QTimer(self)
        self.srv_timer.timeout.connect(self._push_frame)
        self.canvas = BracketCanvas()
        self.scroll = BoardScroll(self)
        self.scroll.setWidget(self.canvas)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.canvas.scroll_area = self.scroll
        self.canvas.changed.connect(self.changed)
        self.canvas.previewRequested.connect(self.show_preview)
        self.scroll.zoomRequested.connect(self.zoom_step)

        # pestaña Archivo
        self.file_btn = QToolButton(self)
        self.file_btn.setObjectName("file")
        self.file_btn.setText("Archivo  ▾")
        self.file_btn.setPopupMode(QToolButton.InstantPopup)
        self.file_btn.setCursor(Qt.PointingHandCursor)
        menu = QMenu(self.file_btn)
        menu.addAction("Importar varias imágenes…   Ctrl+I").triggered.connect(lambda: self.canvas.import_many())
        menu.addAction("Combates por rondas…   F6").triggered.connect(lambda: self.versus.open())
        menu.addSeparator()
        menu.addAction("Guardar torneo        Ctrl+S").triggered.connect(lambda: self.saveRequested.emit())
        menu.addAction("Guardar como…").triggered.connect(lambda: self.saveAsRequested.emit())
        menu.addSeparator()
        obs = menu.addMenu("Para OBS")
        self.act_obs = obs.addAction("Modo OBS (ocultar controles)    F10")
        self.act_obs.setCheckable(True)
        self.act_obs.toggled.connect(self.set_obs_mode)
        bgm = obs.addMenu("Fondo del cuadro")
        grp = QActionGroup(self)
        grp.setExclusive(True)
        for text, col in (("Normal", None), ("Verde croma (#00FF00)", "#00FF00"),
                          ("Magenta croma (#FF00FF)", "#FF00FF"), ("Azul croma (#0000FF)", "#0000FF")):
            a = bgm.addAction(text)
            a.setCheckable(True)
            a.setChecked(col is None)
            grp.addAction(a)
            a.triggered.connect(lambda _=False, c=col: self.set_chroma(c))
        szm = obs.addMenu("Tamaño de la ventana")
        for w, h in ((1280, 720), (1600, 900), (1920, 1080)):
            szm.addAction(f"{w} × {h}").triggered.connect(
                lambda _=False, w=w, h=h: self.windowSizeRequested.emit(w, h))
        self.act_vt = obs.addAction("Fondo transparente (cuadro y combates)")
        self.act_vt.setCheckable(True)
        self.act_vt.toggled.connect(self.set_transparent)
        self.act_srv = obs.addAction("Fuente de navegador (OBS)")
        self.act_srv.setCheckable(True)
        self.act_srv.toggled.connect(self.set_server)
        menu.addSeparator()
        menu.addAction("Volver al inicio").triggered.connect(lambda: self.backRequested.emit())
        self.file_btn.setMenu(menu)

        # nombre del archivo (el título de la ventana se mantiene fijo para que OBS no la pierda)
        self.status = QLabel("", self)
        self.status.setStyleSheet("color:#8C8C8C; font-size:14px; background:transparent;")

        # aviso al entrar en modo OBS
        self.obs_hint = QLabel("Modo OBS activado  ·  F10 o Esc para salir", self)
        self.obs_hint.setStyleSheet("background:rgba(20,20,20,205); color:white; border-radius:16px; "
                                    "padding:8px 18px; font-size:14px;")
        self.obs_hint.hide()

        # barra de zoom
        self.zoombar = QFrame(self)
        self.zoombar.setObjectName("zoombar")
        self.zoombar.setStyleSheet(
            f"QFrame#zoombar {{ background:rgba(255,255,255,235); border:2px solid {ORANGE}; border-radius:22px; }}"
            f"QPushButton {{ background:transparent; border:none; border-radius:16px; color:{ORANGE_D};"
            f" font-weight:700; font-size:18px; min-width:32px; min-height:32px; }}"
            f"QPushButton:hover {{ background:#FFE6D1; }}"
            f"QLabel {{ color:{ORANGE_D}; font-weight:600; min-width:48px; background:transparent; }}")
        zl = QHBoxLayout(self.zoombar)
        zl.setContentsMargins(8, 4, 8, 4)
        zl.setSpacing(2)
        b_out, b_in, b_fit = QPushButton("−"), QPushButton("+"), QPushButton("Ajustar")
        b_fit.setStyleSheet("font-size:13px; min-width:64px;")
        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setAlignment(Qt.AlignCenter)
        for w in (b_out, self.lbl_zoom, b_in, b_fit):
            zl.addWidget(w)
        for b in (b_out, b_in, b_fit):
            b.setCursor(Qt.PointingHandCursor)
        b_out.setToolTip("Alejar (Ctrl + rueda)")
        b_in.setToolTip("Acercar (Ctrl + rueda)")
        b_fit.setToolTip("Ver todo el cuadro en la ventana (Ctrl+0)")
        b_out.clicked.connect(lambda: self.zoom_step(-1))
        b_in.clicked.connect(lambda: self.zoom_step(1))
        b_fit.clicked.connect(self.fit)
        self.zoombar.adjustSize()

        # lápiz (fondo) y cámara (captura)
        self.bg_btn = self._round_button(pencil_icon(ORANGE), "Fondo personalizado")
        self.bg_btn.clicked.connect(lambda: BackgroundDialog(self.canvas).exec())
        self.shot_btn = self._round_button(camera_icon(ORANGE), "Tomar captura del torneo (cuadro completo)")
        self.shot_btn.clicked.connect(self.canvas.take_screenshot)

        # vista previa superpuesta (siempre la última, para quedar encima)
        self.overlay = PreviewOverlay(self)
        self.versus = VersusOverlay(self)
        self.vs_btn = QPushButton("⚔ Combates", self)
        self.vs_btn.setObjectName("soft")
        self.vs_btn.setCursor(Qt.PointingHandCursor)
        self.vs_btn.setToolTip("Combates por rondas (F6)")
        self.vs_btn.clicked.connect(lambda: self.versus.open())
        QShortcut(QKeySequence("F6"), self).activated.connect(lambda: self.versus.open())
        self.overlay.closed.connect(self._preview_closed)

        QShortcut(QKeySequence("Ctrl+I"), self).activated.connect(lambda: self.canvas.import_many())
        QShortcut(QKeySequence("Ctrl+0"), self).activated.connect(self.fit)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self._esc)
        QShortcut(QKeySequence.ZoomIn, self).activated.connect(lambda: self.zoom_step(1))
        QShortcut(QKeySequence.ZoomOut, self).activated.connect(lambda: self.zoom_step(-1))
        self.set_zoom(1.0)

    def _round_button(self, icon, tip):
        b = QPushButton(self)
        b.setObjectName("round")
        b.setFixedSize(52, 52)
        b.setIcon(icon)
        b.setIconSize(QSize(28, 28))
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        return b

    # ----- zoom -----
    def set_zoom(self, z):
        z = clamp(z, self.ZMIN, self.ZMAX)
        c, vp = self.canvas, self.scroll.viewport()
        hb, vb = self.scroll.horizontalScrollBar(), self.scroll.verticalScrollBar()
        fx = (hb.value() + vp.width() / 2) / max(1, c.width())
        fy = (vb.value() + vp.height() / 2) / max(1, c.height())
        c.set_zoom(z)
        c.resize(max(vp.width(), c.minimumWidth()), max(vp.height(), c.minimumHeight()))
        self.lbl_zoom.setText(f"{int(round(z * 100))}%")

        def restore():
            hb.setValue(int(fx * c.width() - vp.width() / 2))
            vb.setValue(int(fy * c.height() - vp.height() / 2))
        QTimer.singleShot(30, restore)

    def zoom_step(self, d):
        if self.obs_mode:
            return
        self.set_zoom(self.canvas.zoom * (1.15 if d > 0 else 1 / 1.15))

    def fit(self):
        if self.obs_mode:
            return
        vp = self.scroll.viewport()
        self.set_zoom(min(vp.width() / DESIGN_W, vp.height() / DESIGN_H) * 0.995)

    # ----- vista previa -----
    def show_preview(self, key, crop=False):
        part = self.canvas.state.get(key)
        if part is not None:
            self.overlay.show_for(part, crop)

    def close_preview(self):
        self.versus.close_overlay()
        self.overlay.close_overlay()

    def _preview_closed(self, modified):
        self.canvas.refresh()
        if modified:
            self.canvas.changed.emit()

    # ----- geometría -----
    TOP_BAR, BOTTOM_BAR = 64, 80

    def paintEvent(self, e):
        qp = QPainter(self)
        if self.canvas.chroma is not None:
            qp.fillRect(self.rect(), QColor(self.canvas.chroma))
            return
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0.0, QColor("#FFFFFF"))
        g.setColorAt(1.0, QColor("#FFE9D6"))
        qp.fillRect(self.rect(), g)

    # ---------------- servidor para la fuente "Navegador" de OBS ----------------
    def set_server(self, on, notify=True):
        if on == (self.server is not None):
            return
        if on:
            srv = MjpegServer()
            try:
                srv.start()
            except OSError as ex:
                obs_log(f"No se pudo iniciar el servidor: {ex}")
                QMessageBox.warning(self, "Servidor para OBS", f"No se pudo iniciar el servidor:\n{ex}")
                self._sync_server_action(False)
                return
            self.server = srv
            self.srv_timer.start(40)
            if notify:
                QApplication.clipboard().setText(srv.url)
                QMessageBox.information(
                self, "Servidor para OBS",
                f"Dirección copiada al portapapeles:\n\n{srv.url}\n\n"
                "En OBS: Fuentes  →  +  →  Navegador, pega la dirección y pon el ancho y alto "
                "de tu lienzo (por ejemplo 1920 × 1080).\n\n"
                "El programa tiene que seguir abierto. No hace falta que la ventana esté visible.")
        else:
            self.srv_timer.stop()
            self.server.stop()
            self.server = None
        self._sync_server_action(on)

    def _sync_server_action(self, on):
        self.act_srv.blockSignals(True)
        self.act_srv.setChecked(on)
        self.act_srv.setText(f"Fuente de navegador: activa ({self.server.url})"
                             if on and self.server else "Fuente de navegador (OBS)")
        self.act_srv.blockSignals(False)

    def _push_frame(self):
        srv = self.server
        if srv is None or srv.clients <= 0:        # solo se dibuja si OBS está conectado
            return
        alpha = False
        if self.versus.isVisible():
            # combates: se envía solo la escena (sin pestañas ni botones), en 16:9 con barras del color de fondo
            v = self.versus.view
            alpha = v.transparent
            v.stream_mode = True
            try:
                if alpha:
                    src = QImage(v.size(), QImage.Format_ARGB32_Premultiplied)
                    src.fill(0)
                    v.render(src, QPoint(), QRegion(), QWidget.RenderFlag.DrawChildren)
                else:
                    src = v.grab().toImage()
            finally:
                v.stream_mode = False
            W0, H0 = 1920, 1080
            img = QImage(W0, H0, QImage.Format_ARGB32_Premultiplied if alpha else QImage.Format_RGB32)
            if alpha:
                img.fill(0)
            qp = QPainter(img)
            qp.setRenderHints(QPainter.RenderHint.SmoothPixmapTransform | QPainter.RenderHint.Antialiasing)
            if alpha:
                pass
            elif self.canvas.chroma is not None:
                qp.fillRect(0, 0, W0, H0, QColor(self.canvas.chroma))
            else:
                gr = QLinearGradient(0, 0, 0, H0)
                gr.setColorAt(0.0, QColor("#150E2B"))
                gr.setColorAt(0.65, QColor("#2A1226"))
                gr.setColorAt(1.0, QColor("#40190A"))
                qp.fillRect(0, 0, W0, H0, gr)
            if not src.isNull():
                k = min(W0 / src.width(), H0 / src.height())
                dw, dh = src.width() * k, src.height() * k
                qp.drawImage(QRectF((W0 - dw) / 2, (H0 - dh) / 2, dw, dh), src)
            qp.end()
        else:
            if self.canvas.transparent:
                alpha = True
                img = self.canvas.grab_alpha()
            else:
                img = self.canvas.grab().toImage()
            if img.width() > 1920:
                img = img.scaledToWidth(1920, Qt.SmoothTransformation)
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        if alpha:
            img.save(buf, "PNG")                   # PNG conserva la transparencia
            srv.push(bytes(buf.data()), "image/png")
        else:
            img.save(buf, "JPG", 85)
            srv.push(bytes(buf.data()), "image/jpeg")

    def set_status(self, text):
        self.status.setText(text)
        self._relayout()

    def set_transparent(self, on):
        self.canvas.transparent_opt = bool(on)
        self.canvas.update()
        self.versus.set_transparent(on)

    def set_chroma(self, color):
        self.canvas.chroma = color
        self.canvas.update()
        self.versus.set_chroma(color)
        self.update()

    def _esc(self):
        if self.versus.isVisible() and not self.obs_mode:
            self.versus.close_overlay()
            return
        if self.overlay.isVisible():
            self.overlay.close_overlay()
        elif self.obs_mode:
            self.set_obs_mode(False)

    def toggle_obs(self):
        self.set_obs_mode(not self.obs_mode)

    def set_obs_mode(self, on):
        """Oculta todos los controles y ajusta el cuadro a la ventana, listo para capturar con OBS."""
        if on == self.obs_mode:
            return
        self.obs_mode = on
        ctrl = (self.file_btn, self.zoombar, self.bg_btn, self.shot_btn, self.status, self.vs_btn)
        if on:
            self._prev_zoom = self.canvas.zoom
            self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.set_zoom(self.ZMIN)           # el cuadro se estira para llenar toda la ventana
            for w in ctrl:
                w.hide()
        else:
            self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            for w in ctrl:
                w.show()
            self.set_zoom(self._prev_zoom)
        self.act_obs.blockSignals(True)
        self.act_obs.setChecked(on)
        self.act_obs.blockSignals(False)
        self._relayout()
        if on:
            self.obs_hint.adjustSize()
            self.obs_hint.move((self.width() - self.obs_hint.width()) // 2,
                               self.height() - self.obs_hint.height() - 24)
            self.obs_hint.show()
            self.obs_hint.raise_()
            QTimer.singleShot(3500, self.obs_hint.hide)
        else:
            self.obs_hint.hide()
        self.versus.set_clean(on)
        self.obsModeChanged.emit(on)

    def resizeEvent(self, e):
        self._relayout()
        super().resizeEvent(e)

    def _relayout(self):
        W, H = self.width(), self.height()
        tb = 0 if self.obs_mode else self.TOP_BAR
        bb = 0 if self.obs_mode else self.BOTTOM_BAR
        m, bs = 22, 52
        self.scroll.setGeometry(0, tb, W, max(50, H - tb - bb))
        self.file_btn.move(m, (tb - self.file_btn.sizeHint().height()) // 2)
        self.status.adjustSize()
        self.status.move(m + self.file_btn.sizeHint().width() + 16, (tb - self.status.height()) // 2)
        yb = H - bb + (bb - bs) // 2
        self.bg_btn.move(W - bs - m, yb)
        self.vs_btn.adjustSize()
        self.vs_btn.move(W - self.vs_btn.width() - m, (tb - self.vs_btn.height()) // 2)
        self.shot_btn.move(W - 2 * bs - m - 10, yb)
        self.zoombar.move(m, H - bb + (bb - self.zoombar.height()) // 2)
        if self.overlay.isVisible():
            self.overlay.relayout()
        if self.versus.isVisible():
            self.versus.relayout()


# ----------------------------------------------------------------------------
# Pantalla de inicio
# ----------------------------------------------------------------------------
class StartPage(QWidget):
    createRequested = Signal()
    loadRequested = Signal()

    def __init__(self):
        super().__init__()
        self.t = 0.0
        self.btn_new = QPushButton("Crear torneo", self)
        self.btn_new.setObjectName("primary")
        self.btn_load = QPushButton("Cargar torneo", self)
        self.btn_load.setObjectName("secondary")
        for b in (self.btn_new, self.btn_load):
            b.setFixedSize(310, 62)
            b.setCursor(Qt.PointingHandCursor)
        self.btn_new.clicked.connect(lambda: self.createRequested.emit())
        self.btn_load.clicked.connect(lambda: self.loadRequested.emit())
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    def _tick(self):
        self.t += 0.09
        self.update()

    def _metrics(self):
        W, H = max(1, self.width()), max(1, self.height())
        ui = clamp(min(W / 1520.0, H / 880.0), 0.5, 1.5)
        lx = max(28, int(W * 0.07))
        px = int(clamp(min(H * 0.115, W * 0.075), 36, 108))
        return W, H, lx, px, ui

    def resizeEvent(self, e):
        W, H, lx, px, ui = self._metrics()
        bw = int(clamp(310 * ui, 190, 340))
        bh = int(clamp(62 * ui, 42, 68))
        fs = int(clamp(18 * ui, 13, 20))
        for b in (self.btn_new, self.btn_load):
            b.setFixedSize(bw, bh)
            b.setStyleSheet(f"font-size:{fs}px; border-radius:{int(bh * 0.32)}px;")
        y0 = int(H * 0.52)
        self.btn_new.move(lx, y0)
        self.btn_load.move(lx, y0 + bh + int(18 * ui))
        super().resizeEvent(e)

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        W, H, lx, px, ui = self._metrics()
        qp.fillRect(self.rect(), QColor("white"))

        # panel naranja decorativo con un mini cuadro
        m = int(clamp(36 * ui, 14, 40))
        panel = QRectF(W * 0.53, m, W * 0.47 - m, H - 2 * m)
        g = QLinearGradient(panel.topLeft(), panel.bottomRight())
        g.setColorAt(0, QColor("#FF9A3D"))
        g.setColorAt(1, QColor("#FF6A00"))
        qp.setPen(Qt.NoPen)
        qp.setBrush(g)
        qp.drawRoundedRect(panel, 40 * ui, 40 * ui)
        self._mini_bracket(qp, panel)

        # título
        f = QFont()
        f.setFamilies(["Segoe UI", "Inter", "Helvetica Neue", "Arial"])
        f.setPixelSize(px)
        f.setWeight(QFont.ExtraBold)
        qp.setFont(f)
        fm = QFontMetrics(f)
        y = int(H * 0.09)
        qp.setPen(QColor(INK))
        qp.drawText(lx, y + fm.ascent(), "Tournament")
        qp.setPen(QColor(ORANGE))
        qp.drawText(lx, y + fm.height() + fm.ascent() - int(px * 0.12), "Maker")
        title_w = fm.horizontalAdvance("Tournament")

        # lema
        f2 = QFont(f)
        f2.setPixelSize(int(clamp(18 * ui, 11, 20)))
        f2.setWeight(QFont.Normal)
        qp.setFont(f2)
        qp.setPen(QColor("#8C8C8C"))
        qp.drawText(lx + 4, int(H * 0.52) - int(26 * ui), "Torneos de 12 participantes, a tu manera.")

        # subtítulo estilo Minecraft
        qp.save()
        qp.translate(lx + title_w - 10, y + px * 0.12)
        qp.rotate(-18)
        s = 1.0 + 0.06 * math.sin(self.t)
        qp.scale(s, s)
        f3 = QFont(f)
        f3.setPixelSize(int(clamp(px * 0.30, 14, 32)))
        f3.setWeight(QFont.Bold)
        qp.setFont(f3)
        txt = "creado por ZABA"
        tw = QFontMetrics(f3).horizontalAdvance(txt)
        qp.setPen(QColor(0, 0, 0, 55))
        qp.drawText(int(-tw / 2) + 2, 2, txt)
        qp.setPen(QColor(ORANGE_D))
        qp.drawText(int(-tw / 2), 0, txt)
        qp.restore()

    def _mini_bracket(self, qp, panel):
        ax, ay = panel.width() * 0.06, panel.height() * 0.08
        inner = panel.adjusted(ax, ay, -ax, -ay)
        cs = bracket_centers(inner.top(), inner.bottom())
        cw = inner.width() / 9.0
        bw = cw * 0.68
        bh = min(bw * 0.72, (inner.height() / 6.0) * 0.64)
        geo = {}
        for side in "LR":
            for r, n in enumerate(ROUNDS):
                col = r if side == "L" else 8 - r
                for i in range(n):
                    geo[(side, r, i)] = QRectF(inner.left() + col * cw + (cw - bw) / 2,
                                               cs[(r, i)] - bh / 2, bw, bh)
        cwid = bw * 1.25
        geo[("C", 0, 0)] = QRectF(inner.left() + 4 * cw + (cw - cwid) / 2,
                                  cs[(3, 0)] - bh * 0.625, cwid, bh * 1.25)
        qp.setPen(QPen(QColor(255, 255, 255, 170), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        for a, b in bracket_links():
            elbow(qp, geo[a], geo[b])
        for k, rect in geo.items():
            qp.setPen(Qt.NoPen)
            if k[0] == "C":
                qp.setBrush(QColor("#FFE08A"))
            else:
                qp.setBrush(QColor(255, 255, 255, 235 if k[1] == 0 else 190))
            qp.drawRoundedRect(rect, 7, 7)


# ----------------------------------------------------------------------------
# Ventana principal
# ----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.path = None
        self.dirty = False
        self.resize(1520, 880)
        self.setMinimumSize(700, 460)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.start = StartPage()
        self.page = TournamentPage()
        self.canvas = self.page.canvas
        self.stack.addWidget(self.start)
        self.stack.addWidget(self.page)

        self.start.createRequested.connect(self.new_tournament)
        self.start.loadRequested.connect(self.load_tournament)
        self.page.backRequested.connect(self.go_home)
        self.page.saveRequested.connect(self.save)
        self.page.saveAsRequested.connect(self.save_as)
        self.page.changed.connect(self.mark_dirty)
        QShortcut(QKeySequence.Save, self).activated.connect(self.save)
        QShortcut(QKeySequence("F11"), self).activated.connect(self.toggle_fullscreen)
        QShortcut(QKeySequence("F10"), self).activated.connect(self.page.toggle_obs)
        self.page.windowSizeRequested.connect(self.set_client_size)
        self.update_title()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def set_client_size(self, w, h):
        """Deja el área de la ventana exactamente en w x h (para igualar el lienzo de OBS)."""
        if self.isFullScreen() or self.isMaximized():
            self.showNormal()
        self.resize(w, h)

    def update_title(self):
        self.setWindowTitle("Tournament Maker")        # título fijo: OBS reconoce siempre la misma ventana
        name = Path(self.path).name if self.path else "Sin guardar"
        self.page.set_status(f"{name}{' *' if self.dirty else ''}")

    def mark_dirty(self):
        self.dirty = True
        self.update_title()

    def maybe_save(self):
        """True si se puede continuar (guardó, descartó o no había cambios)."""
        if self.stack.currentWidget() is self.start or not self.dirty:
            return True
        box = QMessageBox(self)
        box.setWindowTitle("Cambios sin guardar")
        box.setText("Hay cambios sin guardar en el torneo.")
        b_save = box.addButton("Guardar", QMessageBox.AcceptRole)
        b_dis = box.addButton("Descartar", QMessageBox.DestructiveRole)
        box.addButton("Cancelar", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is b_save:
            return self.save()
        return box.clickedButton() is b_dis

    def go_home(self):
        if self.maybe_save():
            self.page.close_preview()
            self.stack.setCurrentWidget(self.start)
            self.update_title()

    def new_tournament(self):
        self.canvas.reset()
        self.page.close_preview()
        self.page.set_zoom(1.0)
        self.path = None
        self.dirty = False
        self.stack.setCurrentWidget(self.page)
        self.update_title()

    def load_tournament(self):
        path, _ = QFileDialog.getOpenFileName(self, "Cargar torneo", "", "Torneo (*.trn)")
        if not path:
            return
        try:
            self.canvas.load_from(path)
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el torneo:\n{ex}")
            return
        self.path = path
        self.dirty = False
        self.page.close_preview()
        self.page.set_zoom(1.0)
        self.stack.setCurrentWidget(self.page)
        self.update_title()

    def save(self):
        if not self.path:
            return self.save_as()
        return self._write(self.path)

    def save_as(self):
        default = (self.canvas.title.text().strip() or "torneo") + ".trn"
        path, _ = QFileDialog.getSaveFileName(self, "Guardar torneo", default, "Torneo (*.trn)")
        if not path:
            return False
        if not path.lower().endswith(".trn"):
            path += ".trn"
        return self._write(path)

    def _write(self, path):
        try:
            self.canvas.save_to(path)
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{ex}")
            return False
        self.path = path
        self.dirty = False
        self.update_title()
        return True

    def closeEvent(self, e):
        if self.maybe_save():
            self.page.set_server(False)
            e.accept()
        else:
            e.ignore()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    f = QFont()
    f.setFamilies(["Segoe UI", "Inter", "Helvetica Neue", "Noto Sans", "Arial"])
    f.setPixelSize(14)
    app.setFont(f)
    app.setStyleSheet(STYLE)
    w = MainWindow()
    scr = app.primaryScreen().availableGeometry()
    w.resize(min(1520, int(scr.width() * 0.92)), min(880, int(scr.height() * 0.92)))
    w.show()
    w.page.set_server(True, notify=False)     # arranca solo y escribe la dirección en el cmd
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
