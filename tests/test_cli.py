import subprocess, sys, os

class TestCLI:
    def test_version(self):
        r = subprocess.run([sys.executable, "-m", "inspector.cli", "--version"], capture_output=True, text=True, timeout=10)
        out = r.stdout + r.stderr
        assert "artifact" in out

    def test_parsers_command(self):
        r = subprocess.run([sys.executable, "-m", "inspector.cli", "parsers"], capture_output=True, text=True, timeout=10)
        out = r.stdout + r.stderr
        assert r.returncode == 0
        assert "PNG" in out

    def test_inspect_nonexistent(self):
        r = subprocess.run([sys.executable, "-m", "inspector.cli", "inspect", "/nonexistent.png"], capture_output=True, text=True, timeout=10)
        assert r.returncode != 0

    def test_inspect_json_flag(self):
        path = "samples/comfyui/001.png"
        if not os.path.exists(path):
            return
        r = subprocess.run([sys.executable, "-m", "inspector.cli", "inspect", path, "--json"], capture_output=True, text=True, timeout=10)
        assert r.returncode == 0
        import json
        data = json.loads(r.stdout)
        assert data["source_tool"] == "ComfyUI"
        assert "generation" in data

    def test_scan_directory(self):
        path = "samples"
        if not os.path.isdir(path):
            return
        r = subprocess.run([sys.executable, "-m", "inspector.cli", "scan", path], capture_output=True, text=True, timeout=30)
        out = r.stdout + r.stderr
        assert r.returncode == 0
        assert "Scanned" in out