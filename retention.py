"""Conventional telemetry products with an explicit encoded byte allowance."""

import struct
import zlib
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass

DAY_MS = 86_400_000
BUDGETS = (256, 512, 1024)
EDGES = (-2000, -500, -50, 50, 500, 2000)
POLICIES = ("equispaced", "strongest", "bin_extrema", "fixed_count20")
ALIGNMENTS = ("nearest20", "prior20")
HEADER = struct.Struct("<4sBBIH8H")
RECORD = struct.Struct("<BIhh")
EXTREMA = struct.Struct("<BBHhh")
FIXED_COUNT = struct.Struct("<BBHHH")
CRC = struct.Struct("<I")
CELLS = tuple((wheel, region) for wheel in range(4) for region in range(7))


@dataclass(frozen=True, slots=True)
class Sample:
    wheel: int
    tick: int
    torque: int
    momentum: int


def quantize(wheel, tick, torque_nm, momentum_nms):
    torque, momentum = round(torque_nm * 100_000), round(momentum_nms * 100)
    if not (-32768 <= torque <= 32767 and -32768 <= momentum <= 32767):
        raise ValueError("Sample exceeds the declared signed 16-bit ranges")
    return Sample(wheel, tick, torque, momentum)


def region(momentum):
    return bisect_right(EDGES, momentum)


def select_equispaced(samples, capacity, day):
    wheels = {wheel: [] for wheel in range(4)}
    for sample in sorted(samples, key=lambda row: row.tick):
        wheels[sample.wheel].append(sample)
    allocated = [0] * 4
    for _ in range(min(capacity, len(samples))):
        available = [wheel for wheel in range(4) if allocated[wheel] < len(wheels[wheel])]
        wheel = min(available, key=lambda item: (allocated[item], item))
        allocated[wheel] += 1
    selected = {}
    for wheel, slots in enumerate(allocated):
        times = [sample.tick for sample in wheels[wheel]]
        for position in range(slots):
            target = day * DAY_MS + (2 * position + 1) * DAY_MS // (2 * slots)
            index = bisect_left(times, target)
            neighbors = wheels[wheel][max(0, index - 1):index + 1]
            sample = min(neighbors, key=lambda item: (abs(item.tick - target), item.tick))
            selected[sample.wheel, sample.tick] = sample
    return sorted(selected.values(), key=lambda row: (row.tick, row.wheel))


def encode(samples, raw_counts, day, alignment, policy, budget):
    if budget not in BUDGETS or len(raw_counts) != 4:
        raise ValueError("Unsupported budget or wheel-count shape")
    admitted = Counter(sample.wheel for sample in samples)
    missing = [raw_counts[wheel] - admitted[wheel] for wheel in range(4)]
    if min(missing) < 0:
        raise ValueError("Admitted counts exceed source counts")
    if policy in ("equispaced", "strongest"):
        capacity = (budget - HEADER.size - CRC.size) // RECORD.size
        if policy == "equispaced":
            selected = select_equispaced(samples, capacity, day)
        else:
            selected = sorted(samples, key=lambda row: (-abs(row.torque), row.tick, row.wheel))[:capacity]
        body = b"".join(RECORD.pack(row.wheel, row.tick - day * DAY_MS, row.torque, row.momentum)
                        for row in selected)
        count = len(selected)
    else:
        cells = defaultdict(list)
        for sample in samples:
            cells[sample.wheel, region(sample.momentum)].append(sample.torque)
        entries = []
        for wheel, cell in CELLS:
            values = cells[wheel, cell]
            if policy == "bin_extrema":
                entries.append(EXTREMA.pack(wheel, cell, len(values), min(values, default=0),
                                            max(values, default=0)))
            elif policy == "fixed_count20":
                entries.append(FIXED_COUNT.pack(wheel, cell, len(values),
                                               max(map(abs, values), default=0),
                                               sum(abs(value) >= 2000 for value in values)))
            else:
                raise ValueError(f"Unknown policy: {policy}")
        body, count = b"".join(entries), len(CELLS)
    tag = POLICIES.index(policy) | (ALIGNMENTS.index(alignment) << 4)
    header = HEADER.pack(b"RWT1", 1, tag, day * 86400, count,
                         *(admitted[wheel] for wheel in range(4)), *missing)
    remaining = budget - len(header) - len(body) - CRC.size
    if remaining < 0:
        raise ValueError("Encoded payload exceeds its byte allowance")
    payload = header + body + bytes(remaining)
    return payload + CRC.pack(zlib.crc32(payload))


def decode(packet):
    if len(packet) not in BUDGETS:
        raise ValueError("Unexpected packet size")
    if CRC.unpack(packet[-CRC.size:])[0] != zlib.crc32(packet[:-CRC.size]):
        raise ValueError("Packet CRC mismatch")
    magic, version, tag, anchor, count, *metadata = HEADER.unpack_from(packet)
    policy_id, alignment_id = tag & 15, tag >> 4
    if magic != b"RWT1" or version != 1 or policy_id >= len(POLICIES) or alignment_id >= len(ALIGNMENTS):
        raise ValueError("Unsupported packet format")
    if anchor % 86400:
        raise ValueError("Day anchor is unaligned")
    policy = POLICIES[policy_id]
    shape = (RECORD, RECORD, EXTREMA, FIXED_COUNT)[policy_id]
    end = HEADER.size + count * shape.size
    if end > len(packet) - CRC.size or any(packet[end:-CRC.size]):
        raise ValueError("Invalid entry count or nonzero padding")
    rows = [shape.unpack_from(packet, HEADER.size + index * shape.size) for index in range(count)]
    admitted, missing = metadata[:4], metadata[4:]
    records, cells = [], {}
    per_wheel = Counter()
    if policy_id < 2:
        seen = set()
        for wheel, offset, torque, momentum in rows:
            if wheel >= 4 or offset >= DAY_MS or (wheel, offset) in seen:
                raise ValueError("Invalid or duplicate sample")
            seen.add((wheel, offset))
            per_wheel[wheel] += 1
            records.append(Sample(wheel, anchor * 1000 + offset, torque, momentum))
        if any(per_wheel[wheel] > admitted[wheel] for wheel in range(4)):
            raise ValueError("Retained count exceeds admitted count")
    else:
        for wheel, cell, number, first, second in rows:
            if (wheel, cell) not in CELLS or (wheel, cell) in cells:
                raise ValueError("Invalid or duplicate summary cell")
            if (number == 0 and (first or second)) or (number > 0 and policy_id == 2 and first > second):
                raise ValueError("Invalid summary extrema")
            if policy_id == 3 and (second > number or first > 32768):
                raise ValueError("Invalid fixed-level summary")
            per_wheel[wheel] += number
            cells[wheel, cell] = (number, first, second)
        if set(cells) != set(CELLS) or any(per_wheel[wheel] != admitted[wheel] for wheel in range(4)):
            raise ValueError("Incomplete or inconsistent summary")
    return {"policy": policy, "alignment": ALIGNMENTS[alignment_id], "day": anchor // 86400,
            "admitted": admitted, "unpaired": missing, "records": records, "cells": cells}


def reference_queries(samples):
    if not samples:
        return {"peak": None, "locations": set(), "counts": {level: Counter() for level in (2000, 3000)}}
    peak = max(abs(row.torque) for row in samples)
    return {
        "peak": peak,
        "locations": {(row.wheel, region(row.momentum)) for row in samples if abs(row.torque) == peak},
        "counts": {level: Counter((row.wheel, region(row.momentum)) for row in samples
                                  if abs(row.torque) >= level) for level in (2000, 3000)},
    }


def decoded_peak(decoded):
    if decoded["records"]:
        records = decoded["records"]
        peak = max(abs(row.torque) for row in records)
        return peak, {(row.wheel, region(row.momentum)) for row in records if abs(row.torque) == peak}
    cell_peaks = {}
    for location, (count, first, second) in decoded["cells"].items():
        if count:
            cell_peaks[location] = max(abs(first), abs(second)) if decoded["policy"] == "bin_extrema" else first
    if not cell_peaks:
        return None, set()
    peak = max(cell_peaks.values())
    return peak, {location for location, value in cell_peaks.items() if value == peak}


def extrema_bounds(count, minimum, maximum, level):
    if count == 0:
        return 0, 0
    if minimum >= level or maximum <= -level:
        return count, count
    if minimum > -level and maximum < level:
        return 0, 0
    endpoints = {minimum, maximum}
    known_bad = sum(abs(value) >= level for value in endpoints)
    known_good = len(endpoints) - known_bad
    return known_bad, count - known_good


def count_bounds(decoded, level):
    if decoded["policy"] in ("equispaced", "strongest"):
        records = decoded["records"]
        retained = Counter(row.wheel for row in records)
        counts = Counter((row.wheel, region(row.momentum)) for row in records if abs(row.torque) >= level)
        all_events_retained = (decoded["policy"] == "strongest" and bool(records)
                               and min(abs(row.torque) for row in records) < level)
        return {cell: (counts[cell], counts[cell] if all_events_retained else
                       counts[cell] + decoded["admitted"][cell[0]] - retained[cell[0]]) for cell in CELLS}
    bounds = {}
    for cell, (count, first, second) in decoded["cells"].items():
        if decoded["policy"] == "bin_extrema":
            bounds[cell] = extrema_bounds(count, first, second, level)
        elif level == 2000:
            bounds[cell] = second, second
        elif first < level:
            bounds[cell] = 0, 0
        else:
            bounds[cell] = 1, second
    return bounds


def score(decoded, truth):
    peak, locations = decoded_peak(decoded)
    result = {
        "nonempty": int(truth["peak"] is not None),
        "peak_exact": int(peak == truth["peak"]),
        "wheel_exact": int({wheel for wheel, _ in locations} == {wheel for wheel, _ in truth["locations"]}),
        "wheel_region_exact": int(locations == truth["locations"]),
        "peak_ge20": int(truth["peak"] is not None and truth["peak"] >= 2000),
    }
    for level in (2000, 3000):
        bounds = count_bounds(decoded, level)
        counts = truth["counts"][level]
        for cell in CELLS:
            low, high = bounds[cell]
            if not low <= counts[cell] <= high:
                raise ValueError(f"Unsound count bound for {decoded['policy']} {cell} at {level}")
        prefix = f"count{level // 100}"
        result[f"{prefix}_exact_cells"] = sum(low == high for low, high in bounds.values())
        result[f"{prefix}_positive_cells"] = sum(counts[cell] > 0 for cell in CELLS)
        result[f"{prefix}_positive_exact"] = sum(counts[cell] > 0 and bounds[cell][0] == bounds[cell][1]
                                                 for cell in CELLS)
        result[f"{prefix}_width"] = sum(high - low for low, high in bounds.values())
    return result
