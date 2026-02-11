"""CAS graphics viewer using pyglet (multiprocessed).

Public API (stable):
- global enable_graphics
- global viewer
- Viewer class with methods: start(), is_alive(), close(),
  add_point(...), add_line(...), add_circle(...), clear().
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import multiprocessing as mp
import queue
import time
from collections import deque
from typing import Deque, Optional, Tuple


# Public global flag
enable_graphics = True

# -----------------------------
# Visible tuning knobs
# -----------------------------

# Max elements kept on screen (circular buffers). Set to None for unlimited.
MAX_POINTS_ON_SCREEN = 1000
MAX_LINES_ON_SCREEN = 500
MAX_CIRCLES_ON_SCREEN = 500

# Base sizes in screen pixels. Actual sizes scale with zoom.
POINT_SIZE = 4.0
LINE_WIDTH = 0.8
MIN_POINT_SIZE = 1.0
MAX_POINT_SIZE = 12.0
MIN_LINE_WIDTH = 0.5
MAX_LINE_WIDTH = 8.0

# Draw-rate control curve (bigger exponent => faster acceleration).
RATE_MIN = 10.0
RATE_STEP_EXPONENT = 1.45
RATE_STEP_SCALE = 18.0

# Auto-camera bounds tuning (trimmed bounds + asymmetric expand/shrink)
FOCUS_POINT_RADIUS = 0.5
FOCUS_SAMPLE_MAX = 400
FOCUS_RADIUS_PERCENTILE = 0.9  # central coverage; 0.9 => 5% trim each side
FOCUS_RADIUS_PADDING = 1.4
FOCUS_UPDATE_INTERVAL = 0.35
FOCUS_MIN_WORLD_SPAN = 16.0
FOCUS_RADIUS_GROW_ALPHA = 0.12
FOCUS_RADIUS_SHRINK_ALPHA = 0.01
FOCUS_RADIUS_SHRINK_ALPHA_FAST = 0.4
FOCUS_RADIUS_SHRINK_FAST_RATIO = 0.6
FOCUS_RADIUS_GROW_EPS = 0.08
FOCUS_RADIUS_SHRINK_EPS = 0.2
ZOOM_IN_MAX_RATE = 250.0
ZOOM_TARGET_EPS = 0.3
ZOOM_TARGET_IN_ALPHA = 0.35
ZOOM_TARGET_OUT_ALPHA = 0.12


# -----------------------------
# Config + state data models
# -----------------------------


Color = Tuple[int, int, int, int]


@dataclass
class ViewerConfig:
    width: int = 1000
    height: int = 700
    title: str = "CasNum Viewer"
    vsync: bool = True
    resizable: bool = True

    background: Color = (18, 18, 22, 255)
    point_color: Color = (230, 230, 230, 255)
    line_color: Color = (140, 200, 255, 255)
    circle_color: Color = (255, 170, 170, 255)
    grid_color: Color = (50, 50, 60, 255)
    axes_color: Color = (120, 120, 140, 255)

    point_size: float = POINT_SIZE
    line_width: float = LINE_WIDTH
    min_point_size: float = MIN_POINT_SIZE
    max_point_size: float = MAX_POINT_SIZE
    min_line_width: float = MIN_LINE_WIDTH
    max_line_width: float = MAX_LINE_WIDTH

    grid_enabled: bool = True
    axes_enabled: bool = True
    grid_target_lines: int = 20
    grid_max_lines: int = 120

    auto_camera: bool = True
    auto_padding: float = 0.12
    camera_smoothing: float = 5.0  # higher = snappier
    camera_smoothing_pos: Optional[float] = 1.3
    camera_smoothing_zoom: Optional[float] = 3.5

    # Set to <= 0 to disable max-zoom-out clamp.
    min_zoom: float = 0.0
    max_zoom: float = 200.0
    zoom_step: float = 1.1  # scroll step base

    queue_maxsize: int = 50000
    drop_policy: str = "drop_oldest"  # drop_oldest | drop_new

    max_points: Optional[int] = MAX_POINTS_ON_SCREEN
    max_lines: Optional[int] = MAX_LINES_ON_SCREEN
    max_circles: Optional[int] = MAX_CIRCLES_ON_SCREEN

    command_rate: Optional[float] = None  # commands per second, None = unlimited
    max_commands_per_frame: Optional[int] = 5000
    rate_min: float = RATE_MIN
    rate_step_exponent: float = RATE_STEP_EXPONENT
    rate_step_scale: float = RATE_STEP_SCALE

    focus_point_radius: float = FOCUS_POINT_RADIUS
    focus_sample_max: int = FOCUS_SAMPLE_MAX
    focus_radius_percentile: float = FOCUS_RADIUS_PERCENTILE
    focus_radius_padding: float = FOCUS_RADIUS_PADDING
    focus_radius_grow_alpha: float = FOCUS_RADIUS_GROW_ALPHA
    focus_radius_shrink_alpha: float = FOCUS_RADIUS_SHRINK_ALPHA
    focus_radius_shrink_alpha_fast: float = FOCUS_RADIUS_SHRINK_ALPHA_FAST
    focus_radius_shrink_fast_ratio: float = FOCUS_RADIUS_SHRINK_FAST_RATIO
    focus_radius_grow_eps: float = FOCUS_RADIUS_GROW_EPS
    focus_radius_shrink_eps: float = FOCUS_RADIUS_SHRINK_EPS
    focus_update_interval: float = FOCUS_UPDATE_INTERVAL
    focus_min_world_span: float = FOCUS_MIN_WORLD_SPAN
    zoom_in_max_rate: float = ZOOM_IN_MAX_RATE
    zoom_target_eps: float = ZOOM_TARGET_EPS
    zoom_target_in_alpha: float = ZOOM_TARGET_IN_ALPHA
    zoom_target_out_alpha: float = ZOOM_TARGET_OUT_ALPHA

    circle_min_segments: int = 24
    circle_max_segments: int = 256
    circle_pixel_step: float = 6.0  # approx pixels per segment when adaptive

    mp_start_method: Optional[str] = None  # spawn | forkserver | None


@dataclass
class CameraState:
    center_x: float = 0.0
    center_y: float = 0.0
    zoom: float = 1.0

    target_x: float = 0.0
    target_y: float = 0.0
    target_zoom: float = 1.0

    auto_mode: bool = True


@dataclass
class SceneState:
    points: Deque[Tuple[float, float]]
    lines: Deque[Tuple[float, float, float, float]]
    circles: Deque[Tuple[float, float, float]]

    max_points: Optional[int] = None
    max_lines: Optional[int] = None
    max_circles: Optional[int] = None

    bbox: Optional[Tuple[float, float, float, float]] = None
    bbox_dirty: bool = False

    points_dirty: bool = True
    lines_dirty: bool = True
    circles_dirty: bool = True
    guides_dirty: bool = True

    last_circle_zoom: float = 1.0
    focus_min_x: float = 0.0
    focus_min_y: float = 0.0
    focus_max_x: float = 0.0
    focus_max_y: float = 0.0
    focus_inited: bool = False
    focus_last_update: float = 0.0

    def clear(self) -> None:
        self.points.clear()
        self.lines.clear()
        self.circles.clear()
        self.bbox = None
        self.bbox_dirty = False
        self.points_dirty = True
        self.lines_dirty = True
        self.circles_dirty = True
        self.guides_dirty = True
        self.focus_inited = False
        self.focus_min_x = 0.0
        self.focus_min_y = 0.0
        self.focus_max_x = 0.0
        self.focus_max_y = 0.0
        self.focus_last_update = 0.0

    def _bbox_update_point(self, x: float, y: float) -> None:
        if self.bbox is None:
            self.bbox = (x, y, x, y)
            return
        min_x, min_y, max_x, max_y = self.bbox
        if x < min_x:
            min_x = x
        if x > max_x:
            max_x = x
        if y < min_y:
            min_y = y
        if y > max_y:
            max_y = y
        self.bbox = (min_x, min_y, max_x, max_y)

    def _bbox_update_line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self._bbox_update_point(x1, y1)
        self._bbox_update_point(x2, y2)

    def _bbox_update_circle(self, cx: float, cy: float, r: float) -> None:
        r = abs(r)
        self._bbox_update_point(cx - r, cy - r)
        self._bbox_update_point(cx + r, cy + r)

    def _maybe_drop(self, buf: Deque, max_len: Optional[int]) -> bool:
        if max_len is None:
            return False
        return len(buf) >= max_len

    def add_point(self, x: float, y: float) -> None:
        dropped = self._maybe_drop(self.points, self.max_points)
        self.points.append((x, y))
        if dropped:
            self.bbox_dirty = True
        else:
            self._bbox_update_point(x, y)
        self.points_dirty = True

    def add_line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        dropped = self._maybe_drop(self.lines, self.max_lines)
        self.lines.append((x1, y1, x2, y2))
        if dropped:
            self.bbox_dirty = True
        else:
            self._bbox_update_line(x1, y1, x2, y2)
        self.lines_dirty = True

    def add_circle(self, cx: float, cy: float, r: float) -> None:
        dropped = self._maybe_drop(self.circles, self.max_circles)
        self.circles.append((cx, cy, r))
        if dropped:
            self.bbox_dirty = True
        else:
            self._bbox_update_circle(cx, cy, r)
        self.circles_dirty = True

    def recompute_bbox(self) -> None:
        self.bbox = None
        for x, y in self.points:
            self._bbox_update_point(x, y)
        for x1, y1, x2, y2 in self.lines:
            self._bbox_update_line(x1, y1, x2, y2)
        for cx, cy, r in self.circles:
            self._bbox_update_circle(cx, cy, r)
        self.bbox_dirty = False



# -----------------------------
# Helper utilities
# -----------------------------


def _clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def _normalize_color(color: Tuple[int, int, int] | Tuple[int, int, int, int]) -> Color:
    if len(color) == 3:
        r, g, b = color
        a = 255
    else:
        r, g, b, a = color
    r = int(_clamp(r, 0, 255))
    g = int(_clamp(g, 0, 255))
    b = int(_clamp(b, 0, 255))
    a = int(_clamp(a, 0, 255))
    return (r, g, b, a)


def _to_float(value) -> Optional[float]:
    try:
        if isinstance(value, complex):
            if value.imag != 0:
                return None
            value = value.real
    except Exception:
        pass
    try:
        f = float(value)
    except Exception:
        return None
    if not math.isfinite(f):
        return None
    return f


def _clamp_zoom(value: float, cfg: ViewerConfig) -> float:
    lo = cfg.min_zoom
    hi = cfg.max_zoom
    if lo is not None and lo > 0 and value < lo:
        value = lo
    if hi is not None and hi > 0 and value > hi:
        value = hi
    return value


# -----------------------------
# Viewer public API
# -----------------------------


class Viewer:
    def __init__(self, cfg: Optional[ViewerConfig] = None) -> None:
        self.cfg = cfg or ViewerConfig()

        methods = mp.get_all_start_methods()
        if self.cfg.mp_start_method in methods:
            start_method = self.cfg.mp_start_method
        elif "forkserver" in methods:
            start_method = "forkserver"
        else:
            start_method = "spawn"

        self._ctx = mp.get_context(start_method)
        self._cmd_q: mp.Queue = self._ctx.Queue(maxsize=self.cfg.queue_maxsize)
        self._gen = self._ctx.Value("i", 0)
        self._proc: Optional[mp.Process] = None

    def start(self) -> None:
        if not enable_graphics:
            return
        if self._proc is not None and self._proc.is_alive():
            return
        self._proc = self._ctx.Process(
            target=_run_viewer_process,
            args=(self._cmd_q, self._gen, self.cfg),
            daemon=False,
        )
        self._proc.start()

    def is_alive(self) -> bool:
        return self._proc is not None and self._proc.is_alive()

    def close(self, timeout: float = 2.0) -> None:
        if self._proc is None:
            return
        if self._proc.is_alive():
            try:
                self._enqueue_control(("close", self._gen.value))
            except Exception:
                pass
            self._proc.join(timeout=timeout)
            if self._proc.is_alive():
                self._proc.terminate()
                self._proc.join(timeout=timeout)
        self._proc = None

    def _enqueue(self, cmd) -> None:
        if not enable_graphics:
            return
        try:
            self._cmd_q.put_nowait(cmd)
        except queue.Full:
            if self.cfg.drop_policy == "drop_oldest":
                try:
                    self._cmd_q.get_nowait()
                except queue.Empty:
                    return
                try:
                    self._cmd_q.put_nowait(cmd)
                except Exception:
                    pass
            # drop_new
        except Exception:
            pass

    def _enqueue_control(self, cmd) -> None:
        if not enable_graphics:
            return
        try:
            self._cmd_q.put_nowait(cmd)
            return
        except queue.Full:
            try:
                self._cmd_q.get_nowait()
            except queue.Empty:
                pass
            try:
                self._cmd_q.put_nowait(cmd)
                return
            except Exception:
                pass
        except Exception:
            pass

    def add_point(self, x, y) -> None:
        if not enable_graphics:
            return
        fx = _to_float(x)
        fy = _to_float(y)
        if fx is None or fy is None:
            return
        gen = self._gen.value
        self._enqueue(("pt", gen, fx, fy))

    def add_line(self, x1, y1, x2, y2) -> None:
        if not enable_graphics:
            return
        fx1 = _to_float(x1)
        fy1 = _to_float(y1)
        fx2 = _to_float(x2)
        fy2 = _to_float(y2)
        if fx1 is None or fy1 is None or fx2 is None or fy2 is None:
            return
        gen = self._gen.value
        self._enqueue(("ln", gen, fx1, fy1, fx2, fy2))

    def add_circle(self, cx, cy, r) -> None:
        if not enable_graphics:
            return
        fcx = _to_float(cx)
        fcy = _to_float(cy)
        fr = _to_float(r)
        if fcx is None or fcy is None or fr is None:
            return
        if fr == 0:
            return
        gen = self._gen.value
        self._enqueue(("ci", gen, fcx, fcy, abs(fr)))

    def clear(self) -> None:
        if not enable_graphics:
            return
        with self._gen.get_lock():
            self._gen.value += 1
            gen = self._gen.value
        self._enqueue_control(("clear", gen))


# -----------------------------
# Viewer process
# -----------------------------


def _run_viewer_process(cmd_q: mp.Queue, gen_value: mp.Value, cfg: ViewerConfig) -> None:
    # Import pyglet only inside the viewer process.
    import pyglet
    from pyglet import gl, shapes
    from pyglet.graphics import Batch, ShaderGroup
    from pyglet.window import key, mouse
    from pyglet.math import Mat4, Vec3

    # Shader for simple 2D colored primitives
    vertex_source = """#version 150 core
    in vec2 position;
    in vec4 colors;
    out vec4 vertex_colors;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        gl_Position = window.projection * window.view * vec4(position, 0.0, 1.0);
        vertex_colors = colors;
    }
    """

    fragment_source = """#version 150 core
    in vec4 vertex_colors;
    out vec4 final_color;

    void main()
    {
        final_color = vertex_colors;
    }
    """

    window = pyglet.window.Window(
        width=cfg.width,
        height=cfg.height,
        caption=cfg.title,
        resizable=cfg.resizable,
        vsync=cfg.vsync,
    )

    # Background
    bg = _normalize_color(cfg.background)
    gl.glClearColor(bg[0] / 255.0, bg[1] / 255.0, bg[2] / 255.0, bg[3] / 255.0)

    program = pyglet.gl.current_context.create_program(
        (vertex_source, "vertex"),
        (fragment_source, "fragment"),
    )
    group = ShaderGroup(program)
    batch = Batch()

    scene = SceneState(
        points=deque(maxlen=cfg.max_points),
        lines=deque(maxlen=cfg.max_lines),
        circles=deque(maxlen=cfg.max_circles),
        max_points=cfg.max_points,
        max_lines=cfg.max_lines,
        max_circles=cfg.max_circles,
    )

    camera = CameraState(
        center_x=0.0,
        center_y=0.0,
        zoom=1.0,
        target_x=0.0,
        target_y=0.0,
        target_zoom=1.0,
        auto_mode=cfg.auto_camera,
    )

    grid_enabled = cfg.grid_enabled
    axes_enabled = cfg.axes_enabled
    paused = True
    step_once = False
    should_close = False
    help_visible = True
    command_rate = cfg.command_rate

    points_vlist = None
    lines_vlist = None
    circles_vlist = None
    grid_vlist = None
    axes_vlist = None

    elements_window: Deque[Tuple[float, int]] = deque()
    elements_per_sec = 0.0

    hud_label = pyglet.text.Label(
        "",
        font_name="Arial",
        font_size=12,
        x=10,
        y=window.height - 10,
        anchor_x="left",
        anchor_y="top",
        color=(230, 230, 230, 255),
        multiline=True,
        width=window.width - 20,
    )

    help_overlay = shapes.Rectangle(
        0, 0, window.width, window.height, color=(10, 10, 14)
    )
    help_overlay.opacity = 220
    help_title = pyglet.text.Label(
        "CAS Viewer Help",
        font_name="Arial",
        font_size=20,
        x=window.width // 2,
        y=window.height - 40,
        anchor_x="center",
        anchor_y="top",
        color=(240, 240, 250, 255),
    )
    help_body_text = "\n".join(
        [
            "Navigation",
            "  Mouse drag (LMB): pan",
            "  Mouse wheel: zoom to cursor",
            "",
            "Playback",
            "  P or Space: pause",
            "  N: step one",
            "  [: slower draw rate",
            "  ]: faster draw rate",
            "  /: unlimited draw rate",
            "",
            "View",
            "  A: toggle auto camera",
            "  R: reset camera",
            "  G: toggle grid",
            "  C: clear",
            "",
            "Other",
            "  H: toggle help",
            "  Q or Esc: quit",
        ]
    )
    help_body = pyglet.text.Label(
        help_body_text,
        font_name="Arial",
        font_size=14,
        x=int(window.width * 0.1),
        y=window.height - 90,
        anchor_x="left",
        anchor_y="top",
        color=(230, 230, 240, 255),
        multiline=True,
        width=int(window.width * 0.8),
    )

    def set_view() -> None:
        view = Mat4().translate(Vec3(window.width / 2.0, window.height / 2.0, 0.0))
        view = view.scale(Vec3(camera.zoom, camera.zoom, 1.0))
        view = view.translate(Vec3(-camera.center_x, -camera.center_y, 0.0))
        window.view = view

    def visible_bounds() -> Tuple[float, float, float, float]:
        half_w = window.width / (2.0 * camera.zoom)
        half_h = window.height / (2.0 * camera.zoom)
        return (
            camera.center_x - half_w,
            camera.center_y - half_h,
            camera.center_x + half_w,
            camera.center_y + half_h,
        )

    def nice_step(span: float, target_lines: int) -> float:
        if span <= 0 or target_lines <= 0:
            return 1.0
        raw = span / float(target_lines)
        exp = math.floor(math.log10(raw)) if raw > 0 else 0
        base = raw / (10 ** exp)
        if base <= 1:
            nice = 1
        elif base <= 2:
            nice = 2
        elif base <= 5:
            nice = 5
        else:
            nice = 10
        return nice * (10 ** exp)

    def rate_step(rate: float) -> float:
        step = (rate ** cfg.rate_step_exponent) / cfg.rate_step_scale
        if step < 1.0:
            step = 1.0
        return step

    def build_grid() -> Tuple[list, list, list, list]:
        if not grid_enabled and not axes_enabled:
            return [], [], [], []
        min_x, min_y, max_x, max_y = visible_bounds()
        span = max(max_x - min_x, max_y - min_y)
        step = nice_step(span, cfg.grid_target_lines)
        # Cap lines
        if step > 0:
            est_lines = int((max_x - min_x) / step) + int((max_y - min_y) / step)
            while est_lines > cfg.grid_max_lines:
                step *= 2.0
                est_lines = int((max_x - min_x) / step) + int((max_y - min_y) / step)

        grid_positions = []
        axes_positions = []
        grid_color = _normalize_color(cfg.grid_color)
        axes_color = _normalize_color(cfg.axes_color)

        if grid_enabled and step > 0:
            start_x = math.floor(min_x / step) * step
            start_y = math.floor(min_y / step) * step
            x = start_x
            while x <= max_x:
                if not axes_enabled or abs(x) > 1e-12:
                    grid_positions.extend([x, min_y, x, max_y])
                x += step
            y = start_y
            while y <= max_y:
                if not axes_enabled or abs(y) > 1e-12:
                    grid_positions.extend([min_x, y, max_x, y])
                y += step

        if axes_enabled:
            # X axis
            axes_positions.extend([min_x, 0.0, max_x, 0.0])
            # Y axis
            axes_positions.extend([0.0, min_y, 0.0, max_y])

        grid_colors = list(grid_color) * (len(grid_positions) // 2)
        axes_colors = list(axes_color) * (len(axes_positions) // 2)
        return grid_positions, grid_colors, axes_positions, axes_colors

    def rebuild_points() -> None:
        nonlocal points_vlist
        positions = []
        colors = []
        color = _normalize_color(cfg.point_color)
        for x, y in scene.points:
            positions.extend([x, y])
            colors.extend(color)
        count = len(scene.points)
        if count == 0:
            if points_vlist is not None:
                points_vlist.delete()
                points_vlist = None
            return
        if points_vlist is None:
            points_vlist = program.vertex_list(
                count,
                gl.GL_POINTS,
                batch=batch,
                group=group,
                position=("f", positions),
                colors=("Bn", colors),
            )
        else:
            if points_vlist.count != count:
                points_vlist.resize(count)
            points_vlist.set_attribute_data("position", positions)
            points_vlist.set_attribute_data("colors", colors)

    def rebuild_lines() -> None:
        nonlocal lines_vlist
        positions = []
        colors = []
        color = _normalize_color(cfg.line_color)
        for x1, y1, x2, y2 in scene.lines:
            positions.extend([x1, y1, x2, y2])
            colors.extend(color)
            colors.extend(color)
        count = len(positions) // 2
        if count == 0:
            if lines_vlist is not None:
                lines_vlist.delete()
                lines_vlist = None
            return
        if lines_vlist is None:
            lines_vlist = program.vertex_list(
                count,
                gl.GL_LINES,
                batch=batch,
                group=group,
                position=("f", positions),
                colors=("Bn", colors),
            )
        else:
            if lines_vlist.count != count:
                lines_vlist.resize(count)
            lines_vlist.set_attribute_data("position", positions)
            lines_vlist.set_attribute_data("colors", colors)

    def rebuild_circles() -> None:
        nonlocal circles_vlist
        positions = []
        colors = []
        color = _normalize_color(cfg.circle_color)
        for cx, cy, r in scene.circles:
            r = abs(r)
            if r == 0:
                continue
            # adaptive segments by pixel length
            segments = int(max(cfg.circle_min_segments, min(cfg.circle_max_segments,
                2 * math.pi * r * camera.zoom / max(cfg.circle_pixel_step, 1e-3)
            )))
            if segments < 6:
                segments = 6
            step = 2 * math.pi / segments
            prev_x = cx + r
            prev_y = cy
            for i in range(1, segments + 1):
                ang = i * step
                x = cx + math.cos(ang) * r
                y = cy + math.sin(ang) * r
                positions.extend([prev_x, prev_y, x, y])
                colors.extend(color)
                colors.extend(color)
                prev_x, prev_y = x, y
        count = len(positions) // 2
        if count == 0:
            if circles_vlist is not None:
                circles_vlist.delete()
                circles_vlist = None
            return
        if circles_vlist is None:
            circles_vlist = program.vertex_list(
                count,
                gl.GL_LINES,
                batch=batch,
                group=group,
                position=("f", positions),
                colors=("Bn", colors),
            )
        else:
            if circles_vlist.count != count:
                circles_vlist.resize(count)
            circles_vlist.set_attribute_data("position", positions)
            circles_vlist.set_attribute_data("colors", colors)
        scene.last_circle_zoom = camera.zoom

    def rebuild_guides() -> None:
        nonlocal grid_vlist, axes_vlist
        grid_positions, grid_colors, axes_positions, axes_colors = build_grid()

        grid_count = len(grid_positions) // 2
        if grid_count == 0:
            if grid_vlist is not None:
                grid_vlist.delete()
                grid_vlist = None
        else:
            if grid_vlist is None:
                grid_vlist = program.vertex_list(
                    grid_count,
                    gl.GL_LINES,
                    batch=batch,
                    group=group,
                    position=("f", grid_positions),
                    colors=("Bn", grid_colors),
                )
            else:
                if grid_vlist.count != grid_count:
                    grid_vlist.resize(grid_count)
                grid_vlist.set_attribute_data("position", grid_positions)
                grid_vlist.set_attribute_data("colors", grid_colors)

        axes_count = len(axes_positions) // 2
        if axes_count == 0:
            if axes_vlist is not None:
                axes_vlist.delete()
                axes_vlist = None
        else:
            if axes_vlist is None:
                axes_vlist = program.vertex_list(
                    axes_count,
                    gl.GL_LINES,
                    batch=batch,
                    group=group,
                    position=("f", axes_positions),
                    colors=("Bn", axes_colors),
                )
            else:
                if axes_vlist.count != axes_count:
                    axes_vlist.resize(axes_count)
                axes_vlist.set_attribute_data("position", axes_positions)
                axes_vlist.set_attribute_data("colors", axes_colors)

    def process_commands(dt: float) -> int:
        nonlocal should_close
        limit = None
        if command_rate is not None:
            limit = max(1, int(command_rate * dt))
        if cfg.max_commands_per_frame is not None:
            limit = cfg.max_commands_per_frame if limit is None else min(limit, cfg.max_commands_per_frame)
        if paused:
            if not step_once:
                return 0
            limit = 1 if limit is None else min(limit, 1)

        elements_added = 0
        count = 0
        while True:
            if limit is not None and count >= limit:
                break
            try:
                cmd = cmd_q.get_nowait()
            except queue.Empty:
                break
            except Exception:
                break

            if not cmd:
                continue
            kind = cmd[0]
            current_gen = gen_value.value
            gen = cmd[1] if len(cmd) > 1 else current_gen
            if gen < current_gen:
                continue

            if kind == "close":
                should_close = True
                break
            if kind == "clear":
                scene.clear()
                scene.guides_dirty = True
                scene.last_circle_zoom = camera.zoom
                continue

            if kind == "pt" and len(cmd) >= 4:
                x, y = cmd[2], cmd[3]
                if math.isfinite(x) and math.isfinite(y):
                    scene.add_point(x, y)
                    elements_added += 1
            elif kind == "ln" and len(cmd) >= 6:
                x1, y1, x2, y2 = cmd[2], cmd[3], cmd[4], cmd[5]
                if math.isfinite(x1) and math.isfinite(y1) and math.isfinite(x2) and math.isfinite(y2):
                    scene.add_line(x1, y1, x2, y2)
                    elements_added += 1
            elif kind == "ci" and len(cmd) >= 5:
                cx, cy, r = cmd[2], cmd[3], cmd[4]
                if math.isfinite(cx) and math.isfinite(cy) and math.isfinite(r) and r != 0:
                    scene.add_circle(cx, cy, abs(r))
                    elements_added += 1

            count += 1
        return elements_added

    def update_camera(dt: float) -> None:
        if scene.bbox_dirty:
            scene.recompute_bbox()

        if camera.auto_mode:
            now = time.perf_counter()
            if (now - scene.focus_last_update) >= cfg.focus_update_interval:
                scene.focus_last_update = now
                xs: list[float] = []
                ys: list[float] = []

                if scene.points:
                    pts = list(scene.points)
                    step = max(1, len(pts) // max(1, cfg.focus_sample_max // 3))
                    for i in range(0, len(pts), step):
                        x, y = pts[i]
                        xs.append(x)
                        ys.append(y)

                if scene.lines:
                    lns = list(scene.lines)
                    step = max(1, len(lns) // max(1, cfg.focus_sample_max // 3))
                    for i in range(0, len(lns), step):
                        x1, y1, x2, y2 = lns[i]
                        xs.extend([x1, x2])
                        ys.extend([y1, y2])

                if scene.circles:
                    circs = list(scene.circles)
                    step = max(1, len(circs) // max(1, cfg.focus_sample_max // 3))
                    for i in range(0, len(circs), step):
                        cx, cy, r = circs[i]
                        r = abs(r)
                        xs.extend([cx - r, cx + r])
                        ys.extend([cy - r, cy + r])

                n = min(len(xs), len(ys))
                if n > 0:
                    xs.sort()
                    ys.sort()
                    p = _clamp(cfg.focus_radius_percentile, 0.0, 1.0)
                    trim = (1.0 - p) * 0.5
                    idx_lo = int(_clamp(trim, 0.0, 0.49) * (n - 1))
                    idx_hi = int(_clamp(1.0 - trim, 0.51, 1.0) * (n - 1))
                    new_min_x = xs[idx_lo]
                    new_max_x = xs[idx_hi]
                    new_min_y = ys[idx_lo]
                    new_max_y = ys[idx_hi]

                    cx = 0.5 * (new_min_x + new_max_x)
                    cy = 0.5 * (new_min_y + new_max_y)
                    half_w = max(1e-6, 0.5 * (new_max_x - new_min_x)) * cfg.focus_radius_padding
                    half_h = max(1e-6, 0.5 * (new_max_y - new_min_y)) * cfg.focus_radius_padding
                    new_min_x = cx - half_w
                    new_max_x = cx + half_w
                    new_min_y = cy - half_h
                    new_max_y = cy + half_h

                    if not scene.focus_inited:
                        scene.focus_min_x = new_min_x
                        scene.focus_min_y = new_min_y
                        scene.focus_max_x = new_max_x
                        scene.focus_max_y = new_max_y
                        scene.focus_inited = True
                    else:
                        cur_w = max(scene.focus_max_x - scene.focus_min_x, 1e-6)
                        cur_h = max(scene.focus_max_y - scene.focus_min_y, 1e-6)
                        new_w = max(new_max_x - new_min_x, 1e-6)
                        new_h = max(new_max_y - new_min_y, 1e-6)
                        ratio_w = new_w / cur_w
                        ratio_h = new_h / cur_h

                        if ratio_w < cfg.focus_radius_shrink_fast_ratio or ratio_h < cfg.focus_radius_shrink_fast_ratio:
                            shrink_alpha = cfg.focus_radius_shrink_alpha_fast
                        else:
                            shrink_alpha = cfg.focus_radius_shrink_alpha
                        expand_alpha = cfg.focus_radius_grow_alpha

                        def update_min(cur: float, new: float, span: float) -> float:
                            delta = new - cur
                            if delta < 0:
                                if abs(delta) / span < cfg.focus_radius_grow_eps:
                                    return cur
                                return cur + delta * expand_alpha
                            if abs(delta) / span < cfg.focus_radius_shrink_eps:
                                return cur
                            return cur + delta * shrink_alpha

                        def update_max(cur: float, new: float, span: float) -> float:
                            delta = new - cur
                            if delta > 0:
                                if abs(delta) / span < cfg.focus_radius_grow_eps:
                                    return cur
                                return cur + delta * expand_alpha
                            if abs(delta) / span < cfg.focus_radius_shrink_eps:
                                return cur
                            return cur + delta * shrink_alpha

                        scene.focus_min_x = update_min(scene.focus_min_x, new_min_x, cur_w)
                        scene.focus_max_x = update_max(scene.focus_max_x, new_max_x, cur_w)
                        scene.focus_min_y = update_min(scene.focus_min_y, new_min_y, cur_h)
                        scene.focus_max_y = update_max(scene.focus_max_y, new_max_y, cur_h)

            if scene.focus_inited:
                world_w = max(scene.focus_max_x - scene.focus_min_x, cfg.focus_min_world_span)
                world_h = max(scene.focus_max_y - scene.focus_min_y, cfg.focus_min_world_span)
                if world_w <= 0:
                    world_w = 1.0
                if world_h <= 0:
                    world_h = 1.0
                camera.target_x = 0.5 * (scene.focus_min_x + scene.focus_max_x)
                camera.target_y = 0.5 * (scene.focus_min_y + scene.focus_max_y)
                zoom_x = window.width / world_w
                zoom_y = window.height / world_h
                desired_zoom = _clamp_zoom(min(zoom_x, zoom_y), cfg)
            elif scene.bbox is not None:
                min_x, min_y, max_x, max_y = scene.bbox
                pad_x = (max_x - min_x) * cfg.auto_padding
                pad_y = (max_y - min_y) * cfg.auto_padding
                if pad_x == 0:
                    pad_x = 1.0
                if pad_y == 0:
                    pad_y = 1.0
                min_x -= pad_x
                max_x += pad_x
                min_y -= pad_y
                max_y += pad_y

                camera.target_x = (min_x + max_x) / 2.0
                camera.target_y = (min_y + max_y) / 2.0

                world_w = max_x - min_x
                world_h = max_y - min_y
                if world_w <= 0:
                    world_w = 1.0
                if world_h <= 0:
                    world_h = 1.0
                zoom_x = window.width / world_w
                zoom_y = window.height / world_h
                desired_zoom = _clamp_zoom(min(zoom_x, zoom_y), cfg)
            else:
                desired_zoom = camera.target_zoom

            # Smooth target zoom with hysteresis to reduce oscillation.
            if desired_zoom <= 0:
                desired_zoom = camera.target_zoom
            if camera.target_zoom <= 0:
                camera.target_zoom = desired_zoom
            else:
                ratio = desired_zoom / camera.target_zoom
                if (1.0 - cfg.zoom_target_eps) <= ratio <= (1.0 + cfg.zoom_target_eps):
                    desired_zoom = camera.target_zoom
                else:
                    if desired_zoom > camera.target_zoom:
                        alpha = cfg.zoom_target_in_alpha
                    else:
                        alpha = cfg.zoom_target_out_alpha
                    desired_zoom = camera.target_zoom + (desired_zoom - camera.target_zoom) * _clamp(alpha, 0.0, 1.0)
            camera.target_zoom = _clamp_zoom(desired_zoom, cfg)

        if camera.auto_mode and camera.target_zoom > camera.zoom and cfg.zoom_in_max_rate > 0:
            max_zoom = camera.zoom * (cfg.zoom_in_max_rate ** dt)
            camera.target_zoom = min(camera.target_zoom, max_zoom)

        # Apply smoothing (separate for position vs zoom)
        pos_smooth = cfg.camera_smoothing_pos if cfg.camera_smoothing_pos is not None else cfg.camera_smoothing
        zoom_smooth = cfg.camera_smoothing_zoom if cfg.camera_smoothing_zoom is not None else cfg.camera_smoothing * 0.6

        if pos_smooth <= 0:
            alpha_pos = 1.0
        else:
            alpha_pos = 1.0 - math.exp(-pos_smooth * dt)
        if zoom_smooth <= 0:
            alpha_zoom = 1.0
        else:
            alpha_zoom = 1.0 - math.exp(-zoom_smooth * dt)

        changed = False
        new_x = camera.center_x + (camera.target_x - camera.center_x) * alpha_pos
        new_y = camera.center_y + (camera.target_y - camera.center_y) * alpha_pos
        new_zoom = camera.zoom + (camera.target_zoom - camera.zoom) * alpha_zoom

        if abs(new_x - camera.center_x) > 1e-9 or abs(new_y - camera.center_y) > 1e-9:
            camera.center_x = new_x
            camera.center_y = new_y
            changed = True
        if abs(new_zoom - camera.zoom) > 1e-9:
            camera.zoom = _clamp_zoom(new_zoom, cfg)
            changed = True

        if changed:
            scene.guides_dirty = True
            # Rebuild circles if zoom changed enough (adaptive segments)
            if abs(camera.zoom - scene.last_circle_zoom) / max(scene.last_circle_zoom, 1e-6) > 0.08:
                scene.circles_dirty = True
                scene.last_circle_zoom = camera.zoom

        if changed:
            set_view()

    @window.event
    def on_draw():
        window.clear()
        point_size = _clamp(cfg.point_size * camera.zoom, cfg.min_point_size, cfg.max_point_size)
        line_width = _clamp(cfg.line_width * camera.zoom, cfg.min_line_width, cfg.max_line_width)
        gl.glPointSize(point_size)
        gl.glLineWidth(line_width)
        batch.draw()
        # Draw HUD/help in screen space (undo world view transform).
        prev_view = window.view
        window.view = Mat4()
        if help_visible:
            help_overlay.draw()
            help_title.draw()
            help_body.draw()
        else:
            hud_label.draw()
        window.view = prev_view

    @window.event
    def on_resize(width, height):
        scene.guides_dirty = True
        hud_label.x = 10
        hud_label.y = height - 10
        hud_label.width = max(10, width - 20)
        help_overlay.width = width
        help_overlay.height = height
        help_title.x = width // 2
        help_title.y = height - 40
        help_body.x = int(width * 0.1)
        help_body.y = height - 90
        help_body.width = max(10, int(width * 0.8))
        set_view()

    @window.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        if buttons & mouse.LEFT:
            camera.center_x -= dx / camera.zoom
            camera.center_y -= dy / camera.zoom
            camera.target_x = camera.center_x
            camera.target_y = camera.center_y
            camera.auto_mode = False
            scene.guides_dirty = True
            set_view()

    @window.event
    def on_mouse_scroll(x, y, scroll_x, scroll_y):
        # Zoom to cursor
        if scroll_y == 0:
            return
        sx = x - window.width / 2.0
        sy = y - window.height / 2.0
        wx = camera.center_x + sx / camera.zoom
        wy = camera.center_y + sy / camera.zoom

        zoom = camera.zoom * (cfg.zoom_step ** scroll_y)
        zoom = _clamp_zoom(zoom, cfg)

        camera.zoom = zoom
        camera.center_x = wx - sx / camera.zoom
        camera.center_y = wy - sy / camera.zoom
        camera.target_x = camera.center_x
        camera.target_y = camera.center_y
        camera.target_zoom = camera.zoom
        camera.auto_mode = False
        scene.guides_dirty = True
        if abs(camera.zoom - scene.last_circle_zoom) / max(scene.last_circle_zoom, 1e-6) > 0.08:
            scene.circles_dirty = True
            scene.last_circle_zoom = camera.zoom
        set_view()

    @window.event
    def on_key_press(symbol, modifiers):
        nonlocal grid_enabled, axes_enabled, paused, step_once, should_close, help_visible, command_rate
        if symbol == key.C:
            # Clear and advance generation to avoid stale commands
            with gen_value.get_lock():
                gen_value.value += 1
            scene.clear()
            scene.guides_dirty = True
        elif symbol == key.G:
            grid_enabled = not grid_enabled
            scene.guides_dirty = True
        elif symbol == key.A:
            camera.auto_mode = not camera.auto_mode
        elif symbol in (key.P, key.SPACE):
            paused = not paused
        elif symbol == key.N:
            step_once = True
        elif symbol == key.R:
            camera.center_x = 0.0
            camera.center_y = 0.0
            camera.zoom = 1.0
            camera.target_x = 0.0
            camera.target_y = 0.0
            camera.target_zoom = 1.0
            camera.auto_mode = False
            scene.guides_dirty = True
            set_view()
        elif symbol == key.BRACKETLEFT:
            if command_rate is None:
                command_rate = cfg.rate_min
            else:
                command_rate = max(cfg.rate_min, command_rate - rate_step(command_rate))
        elif symbol == key.BRACKETRIGHT:
            if command_rate is None:
                command_rate = cfg.rate_min
            else:
                command_rate = command_rate + rate_step(command_rate)
        elif symbol == key.SLASH:
            command_rate = None
        elif symbol == key.H:
            help_visible = not help_visible
        elif symbol in (key.ESCAPE, key.Q):
            should_close = True

    def update(dt):
        nonlocal step_once, should_close, elements_per_sec
        elements_added = process_commands(dt)
        now = time.perf_counter()
        if elements_added > 0:
            elements_window.append((now, elements_added))
        while elements_window and (now - elements_window[0][0]) > 1.0:
            elements_window.popleft()
        if elements_window:
            elements_per_sec = sum(c for _, c in elements_window)
        else:
            elements_per_sec = 0.0

        update_camera(dt)

        if scene.points_dirty:
            rebuild_points()
            scene.points_dirty = False
        if scene.lines_dirty:
            rebuild_lines()
            scene.lines_dirty = False
        if scene.circles_dirty:
            rebuild_circles()
            scene.circles_dirty = False
        if scene.guides_dirty:
            rebuild_guides()
            scene.guides_dirty = False

        rate_text = "unlimited" if command_rate is None else f"{command_rate:.0f}/s"
        hud_label.text = (
            f"elements/sec: {elements_per_sec:.0f}\n"
            f"on screen: pts {len(scene.points)} | lines {len(scene.lines)} | circs {len(scene.circles)}\n"
            f"rate limit: {rate_text} | paused: {paused}"
        )

        if step_once:
            step_once = False

        if should_close:
            window.close()
            pyglet.app.exit()

    set_view()
    pyglet.clock.schedule_interval(update, 1 / 60.0)
    pyglet.app.run()


# Global viewer instance
viewer = Viewer()


__all__ = ["Viewer", "viewer", "enable_graphics"]
