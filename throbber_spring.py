"""Orbit bounce: yellow and cyan Nix trios trade places in a short color loop.

Render: manim -r 480,480 --fps 50 throbber_spring.py SpringBackflip
"""

from __future__ import annotations

import numpy as np
from manim import (
    BLACK, TAU, Scene, VMobject, VGroup, UpdateFromAlphaFunc,
    ManimColor, linear,
)

from throbber_polygon import CLOCKWISE_INDEX_BY_PIECE, PALETTE, lambda_vertices, smootherstep


LOOP_TIME = 2.4  # Geometry time; default 2x playback keeps 60 poses at 50 fps.
# Individual identities return after three rounds, but each trio is now one
# color, so exchanging its members makes every round visually identical.
GEOMETRY_CYCLE = 3.0 * LOOP_TIME
HANDOFF_TIME = LOOP_TIME / 2.0
COHORT_COLORS = (PALETTE[1], PALETTE[4])  # Clockwise odds yellow; evens cyan.
CONTACT_TIME = 0.24
AIR_TIME = HANDOFF_TIME - CONTACT_TIME
JUMP_HEIGHT = 0.82  # Radial displacement, not depth: everything stays flat.
OUTWARD_CLEARANCE = 0.80
CLEARANCE_RAMP = 0.18
CONTACT_SQUEEZE = 0.08
SUPPORT_HEIGHT = 0.045
AIR_STRETCH = 0.03
SPIN_RAMP = 0.08  # About two frames of strong spin-up, then continuous slowing.
SPIN_SETTLE = 0.12
ORBIT_STEP = -TAU / 3.0  # Clockwise two slots: 135 -> 513 -> 351 -> 135.


def clearance_envelope(value: float, ramp: float) -> float:
    """Open space early and retain it into landing, with C2-smooth joins."""
    return smootherstep(value / ramp) * smootherstep((1.0 - value) / ramp)


def spring_segment(
    value: float,
    duration: float,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
) -> float:
    """Quintic interpolation matching position, velocity, and acceleration."""
    x = float(np.clip(value, 0.0, 1.0))
    c0 = start[0]
    c1 = start[1] * duration
    c2 = 0.5 * start[2] * duration * duration
    position = end[0] - c0 - c1 - c2
    velocity = end[1] * duration - c1 - 2.0 * c2
    acceleration = end[2] * duration * duration - 2.0 * c2
    c3 = 10.0 * position - 4.0 * velocity + 0.5 * acceleration
    c4 = -15.0 * position + 7.0 * velocity - acceleration
    c5 = 6.0 * position - 3.0 * velocity + 0.5 * acceleration
    return c0 + x * (c1 + x * (c2 + x * (c3 + x * (c4 + x * c5))))


def tumble_progress(value: float) -> float:
    """A tiny rounded start joins the long, continuously decelerating spin.

    Integrate angular speed (1-x) times a short smoothstep ramp. After the
    brief launch ramp, speed declines through flight. A short landing curve
    also brings angular acceleration to zero without an early angular hold.
    """
    x = float(np.clip(value, 0.0, 1.0))
    r = SPIN_RAMP
    total = 0.5 - 0.5 * r + 0.15 * r * r
    settle_start = 1.0 - SPIN_SETTLE
    if x > settle_start:
        initial = (
            settle_start - 0.5 * settle_start ** 2 - 0.5 * r + 0.15 * r * r
        ) / total
        return spring_segment(
            (x - settle_start) / SPIN_SETTLE,
            SPIN_SETTLE,
            (initial, SPIN_SETTLE / total, -1.0 / total),
            (1.0, 0.0, 0.0),
        )
    if x < r:
        q = x / r
        integral = r * (q ** 3 - 0.5 * q ** 4) - r * r * (0.75 * q ** 4 - 0.4 * q ** 5)
    else:
        integral = x - 0.5 * x * x - 0.5 * r + 0.15 * r * r
    return integral / total


def motion(seconds: float, cohort: int = 0) -> tuple[float, float, float, float]:
    """Return center scale, piece scale, local backflip, and global orbit.

    Each half-cycle has one flying trio and one supporting trio. Contact
    blends the previous landing speed into the next launch speed: the trio
    landing from its high jump compresses first, then the other trio rebounds
    into its high jump. The supporting trio only makes a small, unrotated hop.
    The spring contacts match flight position, velocity, and acceleration.
    Every high jump also advances the trio clockwise by two logo slots.
    """
    t = float(seconds % GEOMETRY_CYCLE)
    half = int(t / HANDOFF_TIME)
    local = t - half * HANDOFF_TIME
    jumping = half % 2 == cohort
    completed_turns = (half + 1 - cohort) // 2
    orbit = ORBIT_STEP * completed_turns
    outgoing_height = JUMP_HEIGHT if jumping else SUPPORT_HEIGHT
    incoming_height = SUPPORT_HEIGHT if jumping else JUMP_HEIGHT

    if local < CONTACT_TIME:
        x = local / CONTACT_TIME
        incoming_speed = 4.0 * incoming_height / AIR_TIME
        outgoing_speed = 4.0 * outgoing_height / AIR_TIME
        incoming_acceleration = -8.0 * incoming_height / AIR_TIME ** 2
        outgoing_acceleration = -8.0 * outgoing_height / AIR_TIME ** 2
        displacement = spring_segment(
            x,
            CONTACT_TIME,
            (0.0, -incoming_speed, incoming_acceleration),
            (0.0, outgoing_speed, outgoing_acceleration),
        )
        # Preserve the original single-reversal center path. A little extra
        # squeeze leaves clearance during contact without the radial nudge
        # that caused repeated direction changes just before takeoff.
        squeeze = CONTACT_SQUEEZE * clearance_envelope(x, 0.20)
        return 1.0 + displacement, 1.0 + displacement - squeeze, 0.0, orbit

    flight = local - CONTACT_TIME
    u = flight / AIR_TIME
    displacement = 4.0 * outgoing_height * u * (1.0 - u)
    # Match the grounded size derivative at takeoff/landing, then keep the
    # airborne lambdas essentially rigid instead of inflating the whole logo.
    piece_scale = 1.0 + AIR_STRETCH * np.tanh(displacement / AIR_STRETCH)
    # Only the launching trio turns. Its spin starts immediately, stays alive
    # through the apex, and finishes at landing, with no airborne holds.
    angle = -TAU * tumble_progress(u) if jumping else 0.0
    if jumping:
        # A wider outer path clears both the standing trio and the other
        # flyers. Add it after size calculation: only the travel grows, not
        # the pieces, the compression depth, or the supporting bounce.
        displacement += OUTWARD_CLEARANCE * clearance_envelope(u, CLEARANCE_RAMP)
        # The arc is fastest at the radial apex, so the pieces sweep through
        # the top of the bounce instead of hanging in place. Both ends are C2.
        orbit += ORBIT_STEP * smootherstep(u)
    return 1.0 + displacement, piece_scale, angle, orbit


def centroid(vertices: np.ndarray) -> np.ndarray:
    following = np.roll(vertices, -1, axis=0)
    cross = vertices[:, 0] * following[:, 1] - following[:, 0] * vertices[:, 1]
    return np.sum((vertices + following) * cross[:, None], axis=0) / (3 * np.sum(cross))


class SpringPiece:
    def __init__(self, index: int, colors: tuple[str, str] = COHORT_COLORS):
        self.index = index
        # Clockwise 1/3/5 are yellow; 2/4/6 are cyan. Same-color partners
        # interchange across the short video seam without a visible reset.
        self.cohort = CLOCKWISE_INDEX_BY_PIECE[index] % 2
        self.color = ManimColor(colors[self.cohort])
        self.vertices = np.asarray(lambda_vertices(index))
        self.landing_poses = [
            np.asarray(lambda_vertices((index - 2 * step) % 6)) for step in range(3)
        ]
        self.center = centroid(self.vertices)
        self.offsets = self.vertices - self.center
        self.shape = VMobject(stroke_width=0, fill_opacity=1, fill_color=self.color)

    def update(self, seconds: float) -> None:
        center_scale, piece_scale, angle, orbit = motion(seconds, self.cohort)
        if angle == 0.0 and center_scale == piece_scale:
            slot = round(orbit / ORBIT_STEP) % 3
            points = self.landing_poses[slot] * center_scale
        else:
            c, s = np.cos(angle), np.sin(angle)
            rotation = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
            points = center_scale * self.center + piece_scale * (self.offsets @ rotation.T)
            c, s = np.cos(orbit), np.sin(orbit)
            orbit_rotation = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
            points = points @ orbit_rotation.T
        self.shape.set_points_as_corners(np.vstack((points, points[0])))


class SpringBackflip(Scene):
    def __init__(
        self,
        *,
        odd_color: str = COHORT_COLORS[0],
        even_color: str = COHORT_COLORS[1],
        playback_speed: float = 2.0,
        **kwargs,
    ):
        if playback_speed <= 0:
            raise ValueError("playback_speed must be positive")
        self.cohort_colors = (odd_color, even_color)
        self.playback_speed = playback_speed
        super().__init__(**kwargs)

    def construct(self) -> None:
        self.camera.background_color = BLACK
        self.camera.frame_width = 12.0
        self.camera.frame_height = 12.0
        pieces = [SpringPiece(index, self.cohort_colors) for index in range(6)]
        logo = VGroup(*(piece.shape for piece in pieces))

        def update(_mob: VGroup, alpha: float) -> None:
            for piece in pieces:
                piece.update(alpha * LOOP_TIME)

        update(logo, 0.0)
        self.add(logo)
        self.play(
            UpdateFromAlphaFunc(logo, update, rate_func=linear),
            run_time=LOOP_TIME / self.playback_speed,
        )
