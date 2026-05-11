import subprocess


def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True)
    except Exception as e:
        return str(e)


print("NVIDIA SMI:")
print(run("nvidia-smi"))

print("Python:")
print(run("python --version"))

print("FFmpeg:")
print(run("ffmpeg -version | head -n 3"))
