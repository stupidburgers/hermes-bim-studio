import os
import sys
import json
import time
import hashlib
import ifcopenshell
import ifcopenshell.geom as geom

IFC_PATH = "C:/Users/Lucas/projects/quantity-takeoff/FAICALVILLE 3Q 128,22 m² - 12X30.ifc"
OUTPUT_DIR = "C:/Users/Lucas/projects/hermes-construtech-studio/spikes"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def inspect_and_takeoff(ifc_file_path):
    t0 = time.time()
    file_hash = sha256_file(ifc_file_path)
    f = ifcopenshell.open(ifc_file_path)
    t_load = time.time() - t0
    
    project = f.by_type("IfcProject")[0]
    project_name = project.Name or "Unnamed Project"
    schema = f.schema
    
    storeys = f.by_type("IfcBuildingStorey")
    storey_info = []
    for s in storeys:
        elev = s.Elevation if hasattr(s, "Elevation") else 0.0
        storey_info.append({"id": s.id(), "name": s.Name, "elevation": elev})
        
    walls = f.by_type("IfcWall")
    slabs = f.by_type("IfcSlab")
    doors = f.by_type("IfcDoor")
    windows = f.by_type("IfcWindow")
    columns = f.by_type("IfcColumn")
    beams = f.by_type("IfcBeam")
    roofs = f.by_type("IfcRoof")
    spaces = f.by_type("IfcSpace")
    
    # Extract quantities and compliance
    compliance_findings = []
    
    # Check spatial containment
    uncontained_count = 0
    for elem in walls + slabs + doors + windows:
        contained = False
        for rel in getattr(elem, "ContainedInStructure", []):
            if rel.is_a("IfcRelContainedInSpatialStructure"):
                contained = True
                break
        if not contained:
            uncontained_count += 1
            
    if uncontained_count > 0:
        compliance_findings.append({
            "check": "Spatial Containment",
            "severity": "WARNING",
            "message": f"{uncontained_count} elements lack explicit IfcRelContainedInSpatialStructure association."
        })
        
    # Geometry processing for mesh visualization
    settings = geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    
    meshes = []
    total_wall_area_approx = 0.0
    total_slab_vol_approx = 0.0
    
    # Process a representative subset of walls and slabs for fast 3D preview
    sample_elements = walls[:40] + slabs[:20] + doors[:10] + windows[:10]
    
    for elem in sample_elements:
        try:
            shape = geom.create_shape(settings, elem)
            verts = shape.geometry.verts
            faces = shape.geometry.faces
            
            # Group vertices into (x, y, z)
            v_list = [round(v, 3) for v in verts]
            f_list = list(faces)
            
            category = elem.is_a()
            color = "#78909c" # default slate
            if category == "IfcWall":
                color = "#cfd8dc"
            elif category == "IfcSlab":
                color = "#90a4ae"
            elif category == "IfcDoor":
                color = "#8d6e63"
            elif category == "IfcWindow":
                color = "#4fc3f7"
                
            meshes.append({
                "id": elem.id(),
                "name": elem.Name or f"{category}_{elem.id()}",
                "type": category,
                "color": color,
                "vertices": v_list,
                "faces": f_list
            })
        except Exception as e:
            continue
            
    # 5D unit cost estimation (Sample benchmark unit rates)
    # Concrete m3: $420/m3, Wall m2: $65/m2, Doors: $250/unit, Windows: $320/unit
    wall_area_est = round(len(walls) * 9.5, 2) # approx m2 based on avg residential panel
    slab_vol_est = round(len(slabs) * 0.45, 2)  # approx m3 based on floor slabs
    
    cost_breakdown = [
        {"item": "Structural Reinforced Concrete (Slabs)", "qty": slab_vol_est, "unit": "m³", "rate": 420.00, "total": round(slab_vol_est * 420.0, 2)},
        {"item": "Masonry Wall Partitions & Facades", "qty": wall_area_est, "unit": "m²", "rate": 65.00, "total": round(wall_area_est * 65.0, 2)},
        {"item": "Internal & External Doors", "qty": len(doors), "unit": "units", "rate": 250.00, "total": round(len(doors) * 250.0, 2)},
        {"item": "Glazed Window Assemblies", "qty": len(windows), "unit": "units", "rate": 320.00, "total": round(len(windows) * 320.0, 2)}
    ]
    
    total_cost = sum(item["total"] for item in cost_breakdown)
    
    summary = {
        "project_name": project_name,
        "schema": schema,
        "sha256": file_hash,
        "load_time_sec": round(t_load, 3),
        "counts": {
            "storeys": len(storeys),
            "spaces": len(spaces),
            "walls": len(walls),
            "slabs": len(slabs),
            "doors": len(doors),
            "windows": len(windows),
            "columns": len(columns),
            "beams": len(beams),
            "roofs": len(roofs)
        },
        "compliance_findings": compliance_findings,
        "cost_takeoff": {
            "items": cost_breakdown,
            "total_cost_usd": total_cost
        },
        "meshes_extracted": len(meshes)
    }
    
    # Write 3D WebGL Viewer HTML
    html_path = os.path.join(OUTPUT_DIR, "viewer_preview.html")
    viewer_html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<title>Hermes BIM Studio — 3D Viewer</title>
<style>
  body {{ margin: 0; overflow: hidden; background: #1a1b26; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #c0caf5; }}
  #viewport {{ width: 100vw; height: 100vh; display: block; }}
  #overlay {{ position: absolute; top: 16px; left: 16px; background: rgba(26, 27, 38, 0.88); border: 1px solid #414868; border-radius: 8px; padding: 14px 18px; max-width: 320px; backdrop-filter: blur(8px); box-shadow: 0 4px 20px rgba(0,0,0,0.4); }}
  h2 {{ margin: 0 0 8px 0; font-size: 16px; color: #7aa2f7; display: flex; align-items: center; gap: 8px; }}
  .badge {{ background: #2ac3de; color: #1a1b26; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; }}
  .stat {{ display: flex; justify-content: space-between; font-size: 13px; margin: 4px 0; }}
  .stat-label {{ color: #7982a9; }}
  .stat-val {{ font-weight: 600; color: #e0af68; }}
  #cost-box {{ margin-top: 10px; padding-top: 8px; border-top: 1px solid #292e42; }}
  #instructions {{ position: absolute; bottom: 16px; right: 16px; background: rgba(26, 27, 38, 0.7); padding: 8px 12px; border-radius: 6px; font-size: 11px; color: #565f89; }}
</style>
<script src=\"https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js\"></script>
<script src=\"https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js\"></script>
</head>
<body>
<div id=\"overlay\">
  <h2>Hermes BIM Studio <span class=\"badge\">LIVE 3D</span></h2>
  <div class=\"stat"><span class=\"stat-label\">Project:</span> <span class=\"stat-val\">{project_name}</span></div>
  <div class=\"stat"><span class=\"stat-label\">Walls:</span> <span class=\"stat-val\">{len(walls)}</span></div>
  <div class=\"stat"><span class=\"stat-label\">Slabs:</span> <span class=\"stat-val\">{len(slabs)}</span></div>
  <div class=\"stat"><span class=\"stat-label\">Doors / Windows:</span> <span class=\"stat-val\">{len(doors)} / {len(windows)}</span></div>
  <div id=\"cost-box\">
    <div class=\"stat"><span class=\"stat-label\">5D Est. Cost:</span> <span class=\"stat-val\" style=\"color: #9ece6a; font-size: 15px;\">${total_cost:,.2f}</span></div>
  </div>
</div>
<div id=\"instructions\">Rotate: Left Click + Drag | Pan: Right Click | Zoom: Scroll</div>
<div id=\"viewport\"></div>

<script>
  const modelData = {json.dumps(meshes)};
  
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x13141f);
  
  const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(25, 20, 30);
  
  const renderer = new THREE.WebGLRenderer({{ antialias: true }});
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  document.getElementById('viewport').appendChild(renderer.domElement);
  
  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  
  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
  scene.add(ambientLight);
  
  const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight1.position.set(40, 60, 40);
  scene.add(dirLight1);
  
  const dirLight2 = new THREE.DirectionalLight(0x7aa2f7, 0.4);
  dirLight2.position.set(-30, -20, -30);
  scene.add(dirLight2);
  
  const grid = new THREE.GridHelper(50, 50, 0x414868, 0x24283b);
  grid.position.y = -0.01;
  scene.add(grid);
  
  const rootGroup = new THREE.Group();
  scene.add(rootGroup);
  
  modelData.forEach(m => {{
    const geom = new THREE.BufferGeometry();
    const vertices = new Float32Array(m.vertices);
    const indices = new Uint32Array(m.faces);
    
    geom.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    geom.setIndex(new THREE.BufferAttribute(indices, 1));
    geom.computeVertexNormals();
    
    const mat = new THREE.MeshStandardMaterial({{
      color: new THREE.Color(m.color),
      roughness: 0.4,
      metalness: 0.1,
      side: THREE.DoubleSide
    }});
    
    const mesh = new THREE.Mesh(geom, mat);
    mesh.userData = {{ id: m.id, name: m.name, type: m.type }};
    rootGroup.add(mesh);
  }});
  
  // Center model
  const box = new THREE.Box3().setFromObject(rootGroup);
  const center = box.getCenter(new THREE.Vector3());
  rootGroup.position.sub(center);
  
  window.addEventListener('resize', () => {{
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }});
  
  function animate() {{
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }}
  animate();
</script>
</body>
</html>"""
    
    with open(html_path, "w", encoding="utf-8") as out:
        out.write(viewer_html)
        
    summary["viewer_html_path"] = html_path
    return summary

if __name__ == "__main__":
    print("Running Hermes BIM Studio Inspector Spike...")
    res = inspect_and_takeoff(IFC_PATH)
    print(json.dumps(res, indent=2))
