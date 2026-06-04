import os

# Kita masukin semua kemungkinan nama folder library & sampah
exclude = {
    "venv", ".venv", "env", ".env", "Lib", "lib",
    "site-packages", "__pycache__", ".git", ".idea"
}

for root, dirs, files in os.walk("."):
    # Potong folder yang masuk list exclude biar gak ditelusurin lebih dalem
    dirs[:] = [d for d in dirs if d not in exclude]

    # Pengaman tambahan: kalau jalurnya mengandung kata di atas, skip!
    if any(x in root.split(os.sep) for x in exclude):
        continue

    level = root.replace(".", "").count(os.sep)
    indent = " " * 4 * level
    print(f"{indent}[{os.path.basename(root) or 'Root'}]")
    sub_indent = " " * 4 * (level + 1)
    for f in files:
        print(f"{sub_indent}- {f}")