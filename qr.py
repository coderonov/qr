import os
import re
import shutil
import sys

try:
    import qrcode
except ImportError:
    sys.exit("pip install qrcode")

if os.name == "nt":
    os.system("")

try:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_CYAN = "\033[36m"
CLR_GREEN = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_GRAY = "\033[90m"


def render(data: str) -> str:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    lines = []
    h = len(matrix)
    w = len(matrix[0]) if h else 0
    term_width = shutil.get_terminal_size((80, 20)).columns
    pad = max(0, (term_width - w) // 2) if term_width > w else 0
    indent = " " * pad

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
        lines.append(indent + "".join(line) + CLR_RESET)

    return "\n".join(lines)


def display_qr(data: str, title: str = ""):
    print()
    if title:
        term_width = shutil.get_terminal_size((80, 20)).columns
        if len(title) <= term_width:
            print(f"{CLR_BOLD}{CLR_GREEN}{title.center(term_width)}{CLR_RESET}\n")
        else:
            print(f"{CLR_BOLD}{CLR_GREEN}{title}{CLR_RESET}\n")
    print(render(data))
    print()


def ask(prompt: str, required: bool = False, default: str = "") -> str:
    prompt_str = f"{CLR_CYAN}{prompt}{CLR_RESET}"
    if default:
        prompt_str += f" {CLR_GRAY}[{default}]{CLR_RESET}"
    prompt_str += ": "
    while True:
        val = input(prompt_str).strip()
        if not val and default:
            return default
        if not val and required:
            print(f"{CLR_YELLOW}Поле обязательно для заполнения.{CLR_RESET}")
            continue
        return val


def create_text_qr():
    data = ask("Введите текст или ссылку", required=True)
    if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", data):
        data = f"mailto:{data}"
        display_qr(data, "Email")
    elif re.match(r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(/.*)?$", data) and not re.match(r"^[a-zA-Z]+://", data):
        data = "https://" + data
        display_qr(data, "Ссылка")
    else:
        display_qr(data, "Ссылка / Текст")


def escape_wifi(text: str) -> str:
    return re.sub(r'([\\;,:\"])', r"\\\1", text)


def create_wifi_qr():
    ssid = ask("Имя сети (SSID)", required=True)
    auth = ask("Тип защиты (1: WPA/WPA2, 2: WEP, 3: Без пароля)", default="1")
    hidden = ask("Скрытая сеть? (y/n)", default="n").lower() == "y"

    if auth == "3":
        auth_type = "nopass"
        password = ""
    elif auth == "2":
        auth_type = "WEP"
        password = ask("Пароль", required=True)
    else:
        auth_type = "WPA"
        password = ask("Пароль", required=True)

    escaped_ssid = escape_wifi(ssid)
    escaped_pass = escape_wifi(password)

    fields = [f"T:{auth_type}", f"S:{escaped_ssid}"]
    if password:
        fields.append(f"P:{escaped_pass}")
    if hidden:
        fields.append("H:true")

    payload = f"WIFI:{';'.join(fields)};;"
    display_qr(payload, f"Wi-Fi: {ssid}")


def create_contact_qr():
    fn = ask("Имя и Фамилия", required=True)
    tel = ask("Телефон")
    email = ask("Email")
    org = ask("Компания / Организация")
    title = ask("Должность")
    note = ask("Заметка")

    parts_name = fn.split(None, 1)
    if len(parts_name) == 2:
        first_name, last_name = parts_name[0], parts_name[1]
    else:
        first_name, last_name = fn, ""

    vcard = [
        "BEGIN:VCARD",
        "VERSION:2.1",
        f"N;CHARSET=UTF-8:{last_name};{first_name};;;",
        f"FN;CHARSET=UTF-8:{fn}",
    ]
    if tel:
        vcard.append(f"TEL;CELL:{tel}")
    if email:
        vcard.append(f"EMAIL;TYPE=HOME:{email}")
    if org:
        vcard.append(f"ORG;CHARSET=UTF-8:{org}")
    if title:
        vcard.append(f"TITLE;CHARSET=UTF-8:{title}")
    if note:
        vcard.append(f"NOTE;CHARSET=UTF-8:{note}")
    vcard.append("END:VCARD")

    payload = "\r\n".join(vcard)
    display_qr(payload, f"Контакт: {fn}")


def show_menu():
    print(f"\n {CLR_GREEN}[1]{CLR_RESET} Ссылка или текст")
    print(f" {CLR_GREEN}[2]{CLR_RESET} Wi-Fi сеть")
    print(f" {CLR_GREEN}[3]{CLR_RESET} Контакт (vCard)")
    print(f" {CLR_YELLOW}[0]{CLR_RESET} Выход\n")


def interactive_mode():
    handlers = {
        "1": create_text_qr,
        "2": create_wifi_qr,
        "3": create_contact_qr,
    }

    while True:
        try:
            show_menu()
            choice = input(f"{CLR_BOLD}> {CLR_RESET}").strip()
            if choice in ("0", "exit", "quit", "q"):
                break
            handler = handlers.get(choice)
            if handler:
                handler()
                input(f"{CLR_GRAY}Нажмите Enter для продолжения...{CLR_RESET}")
            else:
                print(f"{CLR_YELLOW}Неверный ввод.{CLR_RESET}")
        except (EOFError, KeyboardInterrupt):
            print()
            break


def main():
    if len(sys.argv) > 1:
        arg_data = " ".join(sys.argv[1:]).strip()
        if arg_data:
            print(render(arg_data))
        return

    if not sys.stdin.isatty():
        piped_data = sys.stdin.read().strip()
        if piped_data:
            print(render(piped_data))
        return

    interactive_mode()


if __name__ == "__main__":
    main()
