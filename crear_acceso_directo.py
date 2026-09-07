import os
import sys
import subprocess
from pathlib import Path

def crear_acceso_directo():
    project_dir = Path(__file__).resolve().parent
    main_py = project_dir / "main.py"
    icon_path = project_dir / "assets" / "logo.ico"
    
    # Buscar el ejecutable de pythonw (para que no abra la consola negra de comandos)
    venv_pythonw = project_dir / ".venv" / "Scripts" / "pythonw.exe"
    if venv_pythonw.exists():
        python_exe = venv_pythonw
    else:
        python_dir = Path(sys.executable).parent
        sys_pythonw = python_dir / "pythonw.exe"
        python_exe = sys_pythonw if sys_pythonw.exists() else Path(sys.executable)

    # Ruta del escritorio del usuario actual
    desktop_dir = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    if not desktop_dir.exists():
        onedrive_desktop = Path(os.environ.get("USERPROFILE", "")) / "OneDrive" / "Escritorio"
        onedrive_desktop_en = Path(os.environ.get("USERPROFILE", "")) / "OneDrive" / "Desktop"
        desktop_es = Path(os.environ.get("USERPROFILE", "")) / "Escritorio"
        
        if onedrive_desktop.exists():
            desktop_dir = onedrive_desktop
        elif onedrive_desktop_en.exists():
            desktop_dir = onedrive_desktop_en
        elif desktop_es.exists():
            desktop_dir = desktop_es

    shortcut_path = desktop_dir / "Sistema de Ventas.lnk"

    icon_arg = f'$shortcut.IconLocation = "{icon_path}";' if icon_path.exists() else ""
    ps_script = f"""
    $wshShell = New-Object -ComObject WScript.Shell
    $shortcut = $wshShell.CreateShortcut("{shortcut_path}")
    $shortcut.TargetPath = "{python_exe}"
    $shortcut.Arguments = '"{main_py}"'
    $shortcut.WorkingDirectory = "{project_dir}"
    {icon_arg}
    $shortcut.Description = "Sistema de Ventas"
    $shortcut.Save()
    """

    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True)
        print("=" * 60)
        print(" Acceso directo creado exitosamente!")
        print(f" Ubicación: {shortcut_path}")
        print(f" Intérprete: {python_exe}")
        print("=" * 60)
    except Exception as e:
        print(f" Error al crear el acceso directo: {e}")

if __name__ == "__main__":
    crear_acceso_directo()
