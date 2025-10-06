# hospitals_api.py — clean, blueprint-only module
from flask import Blueprint, request, jsonify
import requests
from math import radians, sin, cos, asin, sqrt

# ✅ Define blueprint at top-level
hospitals_bp = Blueprint("hospitals", __name__)

# ---------- Helpers ----------
def geocode_location(q: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": q, "format": "json", "limit": 1}
    r = requests.get(
        url, params=params,
        headers={"User-Agent": "healthbot/1.0"},
        timeout=15
    )
    r.raise_for_status()
    data = r.json()
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name")

def overpass_hospitals(lat, lon, radius_m):
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:{radius_m},{lat},{lon});
      way["amenity"="hospital"](around:{radius_m},{lat},{lon});
      relation["amenity"="hospital"](around:{radius_m},{lat},{lon});
    );
    out center tags;
    """
    r = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=30)
    r.raise_for_status()
    return r.json().get("elements", [])

def match_specialty(tags, specialty):
    if not specialty:
        return True
    s = specialty.lower()
    for k, v in (tags or {}).items():
        if s in f"{k} {v}".lower():
            return True
    return False

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

# ---------- Routes ----------
@hospitals_bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@hospitals_bp.get("/hospitals")
def hospitals():
    near = request.args.get("near") or request.args.get("location")
    specialty = (request.args.get("specialty") or "").strip() or None
    radius_km = float(request.args.get("radius_km", "5"))
    limit = int(request.args.get("limit", "5"))

    if not near:
        return jsonify({"error": "Missing 'near' parameter"}), 400

    geo = geocode_location(near)
    if not geo:
        return jsonify({"error": "Could not geocode location"}), 404
    lat, lon, resolved = geo

    elements = overpass_hospitals(lat, lon, int(radius_km * 1000))

    results = []
    for el in elements:
        tags = el.get("tags", {})
        center = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        if not center.get("lat") or not center.get("lon"):
            continue
        if not match_specialty(tags, specialty):
            continue

        dist = haversine_km(lat, lon, center["lat"], center["lon"])
        name = tags.get("name") or "Unnamed Hospital"
        addr = ", ".join(filter(None, [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:suburb"),
            tags.get("addr:city") or tags.get("addr:town"),
            tags.get("addr:state"),
        ])) or tags.get("addr:full") or ""

        results.append({
            "name": name,
            "distance_km": round(dist, 2),
            "address": addr,
            "phone": tags.get("phone") or tags.get("contact:phone") or "",
            "website": tags.get("website") or "",
            "lat": center["lat"],
            "lon": center["lon"],
        })

    results.sort(key=lambda x: x["distance_km"])
    return jsonify({
        "query": {
            "near": near,
            "specialty": specialty,
            "radius_km": radius_km,
            "resolved_near": resolved
        },
        "count": len(results),
        "results": results[:limit]
    }), 200
