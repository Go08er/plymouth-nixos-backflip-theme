from __future__ import annotations

import numpy as np
from manim import (
    BLACK,
    TAU,
    AnimationGroup,
    Line,
    ManimColor,
    Polygon,
    Scene,
    UpdateFromAlphaFunc,
    VGroup,
    linear,
)


# Fastfetch's six fixed logo colors, clockwise from the upper-left arm.
PALETTE = (
    "#00BFFF",
    "#FFFF00",
    "#0080FF",
    "#FFBF00",
    "#00FFFF",
    "#FF8000",
)

HEX_SIDES = 6
LOOP_TIME = 3.0
PHASE_SLOT = LOOP_TIME / HEX_SIDES
LINE_HOLD = PHASE_SLOT
GROW_TIME = PHASE_SLOT
LOGO_HOLD = 3.0 * PHASE_SLOT
SHRINK_TIME = PHASE_SLOT
PHASE_ORIGIN = PHASE_SLOT / 2.0
SVG_RADIUS = 512.0
PIECE_SCALE = 1.16
LINE_STROKE_WIDTH = 2.0

# Each corner begins before the previous one has completely settled. The
# progressively shorter windows make the smaller, later additions accelerate.
# Broad overlaps keep every addition readable in the 12.5-frame build window.
TRANSITION_START_FRACTIONS = (
    0.00,
    0.17,
    0.32,
    0.46,
    0.59,
    0.70,
    0.79,
)
TRANSITION_END_FRACTIONS = (
    0.38,
    0.43,
    0.56,
    0.68,
    0.79,
    0.89,
    1.00,
)
TRANSITION_STARTS = tuple(GROW_TIME * value for value in TRANSITION_START_FRACTIONS)
TRANSITION_ENDS = tuple(GROW_TIME * value for value in TRANSITION_END_FRACTIONS)

# Official Nix lambda-piece geometry. Six rotated copies form the NixOS logo.
LAMBDA_POINTS = (
    (-624.0, 249.4153162899184),
    (-496.0, 27.712812921102),
    (64.0, 997.6612651596733),
    (-192.0, 997.6612651596733),
    (-320.0, 775.9587617908571),
    (-448.0, 997.6612651596732),
    (-576.0, 997.6612651596732),
    (-640.0, 886.8100134752651),
    (-448.0, 554.2562584220408),
)

CLOCKWISE_INDEX_BY_PIECE = (4, 3, 2, 1, 0, 5)

# Begin on the original long diagonal edge, complete the main lambda stroke,
# then reserve the three final (and fastest) additions for its second leg.
INSERTION_ORDER = (1, 2, 8, 4, 0, 3, 5, 6, 7)


def point(x: float, y: float) -> np.ndarray:
    return np.array([x, y, 0.0])


def clamp01(t: float) -> float:
    return float(np.clip(t, 0.0, 1.0))


def smootherstep(t: float) -> float:
    t = clamp01(t)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def rotate_vector(vertex: np.ndarray, angle: float) -> np.ndarray:
    cosine = np.cos(angle)
    sine = np.sin(angle)
    x, y, _ = vertex
    return point(cosine * x - sine * y, sine * x + cosine * y)


def lambda_vertices(piece_index: int) -> list[np.ndarray]:
    angle = piece_index * TAU / HEX_SIDES
    return [
        rotate_vector(
            point(
                PIECE_SCALE * x / SVG_RADIUS,
                -PIECE_SCALE * y / SVG_RADIUS,
            ),
            angle,
        )
        for x, y in LAMBDA_POINTS
    ]


def polygon_approximation(
    vertices: list[np.ndarray],
    selected: set[int],
) -> np.ndarray:
    """Keep selected corners; place all other anchors along their current chords."""
    count = len(vertices)
    anchors: list[np.ndarray | None] = [None] * count
    ordered = sorted(selected)

    for position, start_index in enumerate(ordered):
        end_index = ordered[(position + 1) % len(ordered)]
        boundary_chain = [start_index]
        while boundary_chain[-1] != end_index:
            boundary_chain.append((boundary_chain[-1] + 1) % count)

        edge_lengths = [
            float(np.linalg.norm(vertices[end] - vertices[start]))
            for start, end in zip(boundary_chain[:-1], boundary_chain[1:], strict=True)
        ]
        total_length = sum(edge_lengths)
        distance_travelled = 0.0

        for chain_position, index in enumerate(boundary_chain[:-1]):
            amount = distance_travelled / total_length
            anchors[index] = (
                (1.0 - amount) * vertices[start_index]
                + amount * vertices[end_index]
            )
            distance_travelled += edge_lengths[chain_position]

    if any(anchor is None for anchor in anchors):
        raise ValueError("Every polygon anchor must be assigned")
    return np.array(anchors)


def growth_clock(t: float, piece_index: int) -> float:
    """Run equal half-second builds and teardowns on a clockwise phase grid."""
    clockwise_index = CLOCKWISE_INDEX_BY_PIECE[piece_index]
    phase_delay = clockwise_index * PHASE_SLOT
    elapsed = (t * LOOP_TIME - phase_delay + PHASE_ORIGIN) % LOOP_TIME
    grow_end = LINE_HOLD + GROW_TIME
    hold_end = grow_end + LOGO_HOLD
    shrink_end = hold_end + SHRINK_TIME

    if elapsed < LINE_HOLD:
        return 0.0
    if elapsed < grow_end:
        return elapsed - LINE_HOLD
    if elapsed < hold_end:
        return GROW_TIME
    if elapsed < shrink_end:
        shrink_progress = (elapsed - hold_end) / SHRINK_TIME
        return GROW_TIME * (1.0 - shrink_progress)
    return 0.0


def make_polygon_piece(piece_index: int) -> tuple[VGroup, list[np.ndarray]]:
    vertices = lambda_vertices(piece_index)
    color = PALETTE[CLOCKWISE_INDEX_BY_PIECE[piece_index]]
    body_z = 10 if piece_index % 2 == 0 else 5

    keyframe_points: list[np.ndarray] = []
    for keyframe_index in range(8):
        selected = set(INSERTION_ORDER[: keyframe_index + 2])
        anchors = polygon_approximation(vertices, selected)
        keyframe = Polygon(*anchors, fill_color=color, stroke_width=0)
        keyframe_points.append(keyframe.points.copy())

    body = Polygon(
        *polygon_approximation(vertices, set(INSERTION_ORDER[:2])),
        fill_color=color,
        fill_opacity=0.0,
        stroke_width=0.0,
    )
    body.set_z_index(body_z)

    seed_line = Line(
        vertices[INSERTION_ORDER[0]],
        vertices[INSERTION_ORDER[1]],
        color=color,
        stroke_width=LINE_STROKE_WIDTH,
    )
    seed_line.set_z_index(body_z + 0.5)
    return VGroup(body, seed_line), keyframe_points


def make_polygon_animation(
    piece: VGroup,
    keyframes: list[np.ndarray],
    piece_index: int,
) -> UpdateFromAlphaFunc:
    color = ManimColor(PALETTE[CLOCKWISE_INDEX_BY_PIECE[piece_index]])
    body_z = 10 if piece_index % 2 == 0 else 5
    if len(keyframes) - 1 != len(TRANSITION_STARTS):
        raise ValueError("Every keyframe transition needs one motion window")

    deltas = [
        next_keyframe - keyframe
        for keyframe, next_keyframe in zip(
            keyframes[:-1], keyframes[1:], strict=True
        )
    ]

    def update(mob: VGroup, t: float) -> None:
        body, seed_line = mob
        clock = growth_clock(t, piece_index)
        amounts = [
            smootherstep((clock - start) / (end - start))
            for start, end in zip(
                TRANSITION_STARTS, TRANSITION_ENDS, strict=True
            )
        ]

        # Cumulative deltas let adjacent corner additions overlap, so velocity
        # transfers continuously instead of dropping to zero at every stage.
        points_now = keyframes[0].copy()
        for delta, amount in zip(deltas, amounts, strict=True):
            points_now += delta * amount
        body.set_points(points_now.copy())

        triangle_amount = amounts[0]
        body.set_fill(color, opacity=1.0)
        body.set_stroke(width=0.0, opacity=0.0)
        seed_line.set_stroke(
            color=color,
            width=LINE_STROKE_WIDTH,
            opacity=1.0 - triangle_amount,
        )

        body.set_z_index(body_z)
        seed_line.set_z_index(body_z + 0.5)

    update(piece, 0.0)
    return UpdateFromAlphaFunc(piece, update, run_time=LOOP_TIME, rate_func=linear)


class NixPolygonBuild(Scene):
    """Keep three lambdas built while one line builds and another deconstructs."""

    def construct(self) -> None:
        self.camera.background_color = BLACK

        piece_data = [make_polygon_piece(i) for i in range(HEX_SIDES)]
        pieces = [piece for piece, _ in piece_data]

        self.add(*pieces)
        self.play(
            AnimationGroup(
                *[
                    make_polygon_animation(piece, keyframes, piece_index)
                    for piece_index, (piece, keyframes) in enumerate(piece_data)
                ]
            ),
            run_time=LOOP_TIME,
            rate_func=linear,
        )
