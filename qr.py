import os
import sys

try:
    import qrcode
except ImportError:
    sys.exit("pip install qrcode")

if os.name == "nt":
    os.system("")


def render(data: str) -> str:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    lines = []
    h = len(matrix)
    w = len(matrix[0]) if h else 0

    for r in range(0, h, 2):
        top_row = matrix[r]
        bot_row = matrix[r + 1] if r + 1 < h else [False] * w
        line = []
        for top, bot in zip(top_row, bot_row):
            if top and bot:
                line.append("\033[30;40m▀")
            elif top and not bot:
                line.append("\033[30;47m▀")
            elif not top and bot:
                line.append("\033[37;40m▀")
            else:
                line.append("\033[37;47m▀")
        lines.append("".join(line) + "\033[0m")

    return "\n".join(lines)


def main():
    while True:
        try:
            link = input("link: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not link:
            continue
        print(f"\n{render(link)}\n")


if __name__ == "__main__":
    main()
