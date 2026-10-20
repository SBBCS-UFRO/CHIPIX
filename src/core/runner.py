# SPDX-License-Identifier: GPL-3.0-or-later
"""External engines with immutable input copies and auditable run manifests."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import uuid
from .formats import read_poses
from .models import DockingRun, SearchBox
from .box_geometry import transform_pdbqt, rotation_matrix
from . import __version__


def digest(path):
    h = hashlib.sha256()
    with open(path,"rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path,data):
    path = Path(path)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    temporary.replace(path)


def resolve_executable(value):
    value = str(value).strip()
    resolved = shutil.which(value)
    if not resolved:
        raise ValueError(f"No se encontró un ejecutable con permisos de ejecución: {value}")
    return str(Path(resolved).resolve())


@dataclass(frozen=True)
class DockingConfig:
    engine: str
    executable: str
    receptor: str
    ligand: str
    ligand_id: str
    context: str
    box: SearchBox
    exhaustiveness: int = 8
    num_modes: int = 9
    energy_range: float = 3.0
    seed: int = 42
    cpu: int = 1
    scoring: str = "vina"

    def validate(self):
        import math
        if self.engine not in ("vina","smina"):
            raise ValueError("Motores de ejecución admitidos: Vina y Smina.")
        if not self.ligand_id.strip() or not self.context.strip():
            raise ValueError("Indica el ID de ligando y el ID de receptor/marco.")
        if self.scoring not in ("vina","vinardo") or (self.engine == "vina" and self.scoring != "vina"):
            raise ValueError("Vinardo está habilitado solamente para Smina en esta versión.")
        if any(type(v) is not int or v <= 0 for v in (self.exhaustiveness,self.num_modes,self.cpu)):
            raise ValueError("Exhaustividad, poses y CPU deben ser enteros positivos.")
        if type(self.seed) is not int or not 1 <= self.seed <= 2147483647:
            raise ValueError("Usa una semilla entre 1 y 2147483647.")
        if not math.isfinite(self.energy_range) or self.energy_range <= 0:
            raise ValueError("El rango energético debe ser finito y positivo.")
        for value in (self.receptor,self.ligand):
            p = Path(value)
            if p.suffix.lower() != ".pdbqt" or not p.is_file() or p.stat().st_size == 0:
                raise ValueError("Receptor y ligando deben ser archivos PDBQT preparados y no vacíos.")
        resolve_executable(self.executable)


def prepare_run(config, output_root):
    config.validate()
    executable = resolve_executable(config.executable)
    identifier = f"{config.engine}-{uuid.uuid4().hex[:12]}"
    directory = Path(output_root).expanduser().resolve()/identifier
    directory.mkdir(parents=True,exist_ok=False)
    receptor, ligand = directory/"receptor.pdbqt", directory/"ligand.pdbqt"
    shutil.copyfile(config.receptor,receptor)
    shutil.copyfile(config.ligand,ligand)
    output = directory/"poses.pdbqt"
    rotated = any(v % 360 for v in config.box.rotation)
    input_hashes = {"receptor.pdbqt":digest(receptor), "ligand.pdbqt":digest(ligand)}
    frame = None
    if rotated:
        frame = {"center":config.box.center,"rotation":config.box.rotation,
                 "matrix_local_to_scene":rotation_matrix(config.box.rotation),
                 "coordinate_precision_angstrom":0.001}
        for path in (receptor, ligand):
            local_path = path.with_name("engine-"+path.name)
            local_path.write_text(transform_pdbqt(path.read_text(encoding="utf-8"),config.box),encoding="utf-8")
            input_hashes[local_path.name] = digest(local_path)
        receptor, ligand = directory/"engine-receptor.pdbqt", directory/"engine-ligand.pdbqt"
        output = directory/"engine-poses.pdbqt"
    args = [executable,"--receptor",str(receptor),"--ligand",str(ligand)]
    for axis,center,size in zip("xyz",(0.,0.,0.) if rotated else config.box.center,config.box.size):
        args += [f"--center_{axis}",str(center),f"--size_{axis}",str(size)]
    args += ["--out",str(output),"--exhaustiveness",str(config.exhaustiveness),
             "--num_modes",str(config.num_modes),"--energy_range",str(config.energy_range),
             "--seed",str(config.seed),"--cpu",str(config.cpu)]
    if config.engine == "smina":
        args += ["--scoring",config.scoring]
    data = {"schema_version":1,"application":{"name":"CHIPIX","version":__version__},
            "id":identifier,"state":"prepared","created":now(),
            "config":asdict(config),"command":args,"executable_sha256":digest(executable),
            "platform":platform.platform(),"python":platform.python_version(),
            "inputs":input_hashes,
            "output":"poses.pdbqt","log":"engine.log"}
    if frame:
        data.update(coordinate_frame=frame,engine_output=output.name)
    manifest = directory/"run.json"
    write_json(manifest,data)
    return manifest


def update_run(manifest,**updates):
    data = json.loads(Path(manifest).read_text(encoding="utf-8"))
    data.update(updates)
    write_json(manifest,data)
    return data


def finish_run(manifest,exit_code,cancelled=False):
    data = json.loads(Path(manifest).read_text(encoding="utf-8"))
    if cancelled:
        update_run(manifest,state="cancelled",exit_code=exit_code,finished=now())
        return None
    if exit_code != 0:
        update_run(manifest,state="failed",exit_code=exit_code,finished=now())
        raise ValueError(f"El motor terminó con código {exit_code}. Revisa {Path(manifest).parent/'engine.log'}")
    try:
        if "coordinate_frame" in data:
            directory = Path(manifest).parent
            raw = directory/data["engine_output"]
            box = SearchBox(**data["config"]["box"])
            (directory/data["output"]).write_text(transform_pdbqt(raw.read_text(encoding="utf-8"),box,inverse=True),encoding="utf-8")
            update_run(manifest,engine_output_sha256=digest(raw))
        poses = read_poses(Path(manifest).parent/data["output"])
    except (ValueError,OSError) as error:
        update_run(manifest,state="failed",exit_code=exit_code,error=str(error),finished=now())
        raise ValueError(f"La salida del motor es inválida: {error}") from error
    update_run(manifest,state="completed",exit_code=0,finished=now(),pose_count=len(poses),
               output_sha256=digest(Path(manifest).parent/data["output"]))
    return load_run(manifest)


def load_run(manifest):
    manifest = Path(manifest).resolve()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("state") != "completed":
        raise ValueError("Se requiere un run.json completado de CHIPIX 1.0.0.")
    output = (manifest.parent/data["output"]).resolve()
    if output.parent != manifest.parent:
        raise ValueError("La salida debe estar dentro de la carpeta de ejecución.")
    if digest(output) != data["output_sha256"]:
        raise ValueError("El resultado fue modificado: su SHA-256 no coincide con run.json.")
    config = data["config"]
    return DockingRun(data["id"],config["engine"],config["ligand_id"],config["context"],
                      read_poses(output,data.get("score_field","")),str(output),str(manifest),data["output_sha256"])


def import_run(path,engine,ligand_id,context,output_root,score_field=""):
    """Snapshot externally generated results so they can be recovered like local runs."""
    if not ligand_id.strip() or not context.strip():
        raise ValueError("Indica ID de ligando e ID de receptor/marco para importar.")
    path = Path(path).resolve()
    poses = read_poses(path,score_field)
    identifier = f"import-{uuid.uuid4().hex[:12]}"
    directory = Path(output_root).expanduser().resolve()/identifier
    directory.mkdir(parents=True,exist_ok=False)
    output = directory/("poses"+path.suffix.lower())
    shutil.copyfile(path,output)
    data = {"schema_version":1,"application":{"name":"CHIPIX","version":__version__},
            "id":identifier,"state":"completed","imported":True,
            "created":now(),"finished":now(),"original_source":str(path),"score_field":score_field,
            "config":{"engine":engine,"ligand_id":ligand_id.strip(),"context":context.strip()},
            "output":output.name,"output_sha256":digest(output),"pose_count":len(poses)}
    manifest = directory/"run.json"
    write_json(manifest,data)
    return load_run(manifest)


def execute(config,output_root):
    """Synchronous entry point for batch use; GUI uses QProcess instead."""
    manifest = prepare_run(config,output_root)
    data = update_run(manifest,state="running",started=now())
    try:
        with open(manifest.parent/"engine.log","wb") as log:
            result = subprocess.run(data["command"],cwd=manifest.parent,stdout=log,stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL,check=False)
    except OSError as error:
        update_run(manifest,state="failed",error=str(error),finished=now())
        raise
    return finish_run(manifest,result.returncode)
