from __future__ import annotations

from ..road_net import (
    ExtendedLane,
    Lane,
    LaneLink,
    LaneLike,
    RoadNet,
    TrafficLight,
)


def build_extended_lanes(
    road_net: RoadNet,
    min_length: float = 50,
    max_distance: float | None = None,
) -> RoadNet:
    """
    Build "extended lanes" for every traffic light of the given road net.

    For every signalized junction:
      - each incoming lane whose own length is shorter than `min_length` and
        whose upstream junction is **not** signalized is extended upstream
        through non-signalized junctions until the accumulated approach
        length reaches `min_length` (or the chain is blocked by another
        signal / the end of the network);
      - each outgoing lane is extended downstream through non-signalized
        junctions up to the next signalized junction.
    Both walks are additionally capped at `max_distance` meters from the head
    lane (when given), so extensions (and, through them, neighbor discovery)
    are limited by distance rather than hop count.

    The result is attached to the road net *without modifying* the original
    lanes / links:
        - `road_net.extended_lane_bank`:  head lane id -> ExtendedLane
        - `road_net.incoming_lane_map`:   lane id -> ExtendedLane (only for
          extended head lanes)
        - `road_net.outgoing_extended_lane_bank`: head lane id -> ExtendedLane
          of the downstream (outgoing) extension
        - `road_net.outgoing_lane_map`:   lane id -> ExtendedLane used as the
          extended outgoing of this lane (or the lane itself)
        - `road_net.outgoing_map`:        lane id / extended lane id ->
          list of outgoing LaneLike
        - `road_net.extended_lane_max_distance`: the distance cap used
        - `traffic_light.controlled_links_extended`: LaneLinks whose
          `from_lane` / `to_lane` may be `ExtendedLane`
        - `traffic_light_phase.available_links_extended`: the extended
          LaneLinks controlled by that phase (aligned with `available_links`)

    Args:
        road_net (RoadNet): the road net to extend (e.g. the simplified net
            used by the SC-MP controller / monitors).
        min_length (float): minimum approach length (in meters) to consider a
            lane "long enough" not to need extension. Defaults to 50.
        max_distance (float | None): maximum distance (in meters) from the
            head lane that incoming / outgoing extensions may reach. `None`
            means no cap.

    Returns:
        RoadNet: the same object, with the extended structures attached.
    """
    road_net.extended_lane_max_distance = max_distance

    tl_by_junction: dict[str, TrafficLight] = {}
    for tl in road_net.traffic_lights:
        for junction in tl.junctions:
            tl_by_junction[junction.id] = tl

    extended: dict[str, ExtendedLane] = {}

    # ---- pass 1: incoming extended lanes ----
    for tl in road_net.traffic_lights:
        for junction in tl.junctions:
            for lane in junction.incoming_lanes:
                if lane.id in extended:
                    continue
                ext = _extend_incoming(lane, tl_by_junction, min_length, max_distance)
                if ext is not None and len(ext.lanes) > 1:
                    extended[lane.id] = ext

    road_net.extended_lane_bank = dict(extended)
    road_net.incoming_lane_map = dict(extended)

    # every lane that participates in some extended lane maps to it
    participating: dict[str, ExtendedLane] = {}
    for ext in extended.values():
        for lane in ext.lanes:
            participating.setdefault(lane.id, ext)

    # ---- pass 2: outgoing extended lanes (downstream, distance-limited) ----
    outgoing_extended: dict[str, ExtendedLane] = {}
    for tl in road_net.traffic_lights:
        for junction in tl.junctions:
            for lane in junction.outgoing_lanes:
                if lane.id in outgoing_extended:
                    continue
                ext = _extend_downstream(lane, tl_by_junction, max_distance)
                if ext is not None and len(ext.lanes) > 1:
                    outgoing_extended[lane.id] = ext
    road_net.outgoing_extended_lane_bank = dict(outgoing_extended)

    # every lane that participates in some outgoing extension maps to it
    outgoing_participating: dict[str, ExtendedLane] = {}
    for ext in outgoing_extended.values():
        for lane in ext.lanes:
            outgoing_participating.setdefault(lane.id, ext)

    outgoing_lane_map: dict[str, LaneLike] = {}
    for tl in road_net.traffic_lights:
        for junction in tl.junctions:
            for lane in junction.outgoing_lanes:
                outgoing_lane_map[lane.id] = (
                    outgoing_participating.get(lane.id)
                    or participating.get(lane.id)
                    or lane
                )
    road_net.outgoing_lane_map = outgoing_lane_map

    # ---- pass 3: extended LaneLinks per traffic light / phase ----
    for tl in road_net.traffic_lights:
        pair_to_link: dict[tuple[str, str], LaneLink] = {}
        for link in tl.controlled_links:
            from_like = extended.get(link.from_lane.id, link.from_lane)
            to_like = outgoing_lane_map.get(link.to_lane.id, link.to_lane)
            new_link = LaneLink(
                from_lane=from_like,
                to_lane=to_like,
                link_lane=link.link_lane,
                type=link.type,
            )
            pair_to_link[(link.from_lane.id, link.to_lane.id)] = new_link
        tl.controlled_links_extended = list(pair_to_link.values())
        for phase in tl.phases:
            phase.available_links_extended = [
                pair_to_link[(link.from_lane.id, link.to_lane.id)]
                for link in phase.available_links
            ]

    # ---- pass 4: incoming -> outgoing connection map ----
    outgoing_map: dict[str, list[LaneLike]] = {}
    for tl in road_net.traffic_lights:
        for junction in tl.junctions:
            for lane in junction.incoming_lanes:
                outgoings = []
                for link in lane.links:
                    to_like = outgoing_lane_map.get(link.to_lane.id, link.to_lane)
                    if to_like not in outgoings:
                        outgoings.append(to_like)
                outgoing_map[lane.id] = outgoings
    for ext in extended.values():
        ext.outgoing = outgoing_map.get(ext.head_lane.id, [])
        outgoing_map[ext.id] = ext.outgoing
    road_net.outgoing_map = outgoing_map

    return road_net


def _extend_incoming(
    lane: Lane,
    tl_by_junction: dict[str, TrafficLight],
    min_length: float,
    max_distance: float | None,
) -> ExtendedLane | None:
    """
    Extend `lane` upstream through non-signalized junctions until the longest
    chain reaches `min_length` (or `max_distance`, whichever is smaller).
    Returns None when no upstream extension is needed (i.e. the lane itself
    is already long enough).
    """
    if lane.length >= min_length or lane.from_junction.id in tl_by_junction:
        return None

    lanes: list[Lane] = [lane]
    seen = {lane.id}
    frontier: list[tuple[Lane, float]] = [(lane, lane.length)]

    while frontier:
        next_frontier: list[tuple[Lane, float]] = []
        for cur_lane, acc_len in frontier:
            if acc_len >= min_length:
                continue
            if max_distance is not None and acc_len >= max_distance:
                continue
            for upstream in cur_lane.upstream_lanes:
                if upstream.id in seen:
                    continue
                # do not cross another signalized junction
                if upstream.from_junction.id in tl_by_junction:
                    continue
                seen.add(upstream.id)
                lanes.append(upstream)
                next_frontier.append((upstream, acc_len + upstream.length))
        if not next_frontier:
            break
        frontier = next_frontier

    if len(lanes) <= 1:
        return None

    total_length = max(acc for _, acc in frontier) if frontier else lane.length
    if len(lanes) == 1:
        total_length = lane.length
    return ExtendedLane(
        head_lane=lane,
        lanes=tuple(lanes),
        length=total_length,
    )


def _extend_downstream(
    lane: Lane,
    tl_by_junction: dict[str, TrafficLight],
    max_distance: float | None,
) -> ExtendedLane | None:
    """
    Extend `lane` downstream through non-signalized junctions up to the next
    signalized junction (whose approach lane is included, but not crossed),
    capped at `max_distance` meters from the start of `lane`. Returns None
    when there is nothing to extend (the lane already ends at a signal or no
    downstream corridor exists within the limit).
    """
    if lane.to_junction.id in tl_by_junction:
        return None

    lanes: list[Lane] = [lane]
    seen = {lane.id}
    frontier: list[tuple[Lane, float]] = [(lane, lane.length)]
    max_acc = lane.length

    while frontier:
        next_frontier: list[tuple[Lane, float]] = []
        for cur_lane, acc_len in frontier:
            if max_distance is not None and acc_len >= max_distance:
                continue
            for downstream in cur_lane.downstream_lanes:
                if downstream.id in seen:
                    continue
                seen.add(downstream.id)
                lanes.append(downstream)
                new_acc = acc_len + downstream.length
                max_acc = max(max_acc, new_acc)
                if downstream.to_junction.id in tl_by_junction:
                    # reached the next signal: include this approach lane but
                    # do not cross the signal
                    continue
                next_frontier.append((downstream, new_acc))
        if not next_frontier:
            break
        frontier = next_frontier

    if len(lanes) <= 1:
        return None
    return ExtendedLane(
        head_lane=lane,
        lanes=tuple(lanes),
        length=max_acc,
    )
