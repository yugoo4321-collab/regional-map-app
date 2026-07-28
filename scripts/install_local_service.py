from __future__ import annotations

import argparse
import os
import plistlib
import shlex
import signal
import subprocess
import time
import urllib.request
from pathlib import Path


LABEL = "com.yugo.regional-map-app"
PROJECT_DIR = Path.home() / "Documents" / "regional-map-app"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG_DIR = PROJECT_DIR / ".logs"
PORT = 8501


def domain() -> str:
    return f"gui/{os.getuid()}"


def run(
    arguments: list[str],
    *,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        check=check,
        text=True,
        capture_output=capture,
    )


def health_ok() -> bool:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{PORT}/_stcore/health",
            timeout=1.5,
        ) as response:
            return response.status == 200
    except Exception:
        return False


def listener_pids() -> list[int]:
    result = run(
        ["lsof", "-tiTCP:8501", "-sTCP:LISTEN"],
        check=False,
        capture=True,
    )
    return [
        int(item)
        for item in result.stdout.split()
        if item.strip().isdigit()
    ]


def stop_manual_streamlit() -> None:
    for pid in listener_pids():
        command = run(
            ["ps", "-p", str(pid), "-o", "command="],
            check=False,
            capture=True,
        ).stdout.strip()

        if "streamlit" in command.lower() and "app.py" in command:
            os.kill(pid, signal.SIGTERM)
            for _ in range(20):
                if pid not in listener_pids():
                    break
                time.sleep(0.25)
        elif pid in listener_pids():
            raise RuntimeError(
                f"ポート{PORT}を別の処理が使用しています: PID {pid} / {command}"
            )


def plist_payload() -> dict:
    python_path = PROJECT_DIR / ".venv" / "bin" / "python"
    app_path = PROJECT_DIR / "app.py"

    if not python_path.exists():
        raise FileNotFoundError(f"{python_path} が見つかりません")
    if not app_path.exists():
        raise FileNotFoundError(f"{app_path} が見つかりません")

    command = (
        f"cd {shlex.quote(str(PROJECT_DIR))} && "
        f"exec {shlex.quote(str(python_path))} -m streamlit run app.py "
        "--server.headless true "
        "--server.address 127.0.0.1 "
        f"--server.port {PORT} "
        "--browser.gatherUsageStats false"
    )

    return {
        "Label": LABEL,
        "ProgramArguments": ["/bin/zsh", "-lc", command],
        "WorkingDirectory": str(PROJECT_DIR),
        "RunAtLoad": True,
        "KeepAlive": {
            "SuccessfulExit": False,
            "Crashed": True,
        },
        "ThrottleInterval": 5,
        "ProcessType": "Interactive",
        "StandardOutPath": str(LOG_DIR / "streamlit.out.log"),
        "StandardErrorPath": str(LOG_DIR / "streamlit.err.log"),
        "EnvironmentVariables": {
            "PYTHONUNBUFFERED": "1",
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
        },
    }


def bootout() -> None:
    run(
        ["launchctl", "bootout", domain(), str(PLIST_PATH)],
        check=False,
        capture=True,
    )


def install() -> None:
    if os.uname().sysname != "Darwin":
        raise RuntimeError("この自動起動設定はmacOS専用です")

    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    bootout()
    stop_manual_streamlit()

    with PLIST_PATH.open("wb") as file:
        plistlib.dump(plist_payload(), file, sort_keys=False)

    run(["launchctl", "bootstrap", domain(), str(PLIST_PATH)])
    run(["launchctl", "enable", f"{domain()}/{LABEL}"], check=False)
    run(
        ["launchctl", "kickstart", "-k", f"{domain()}/{LABEL}"],
        check=False,
    )

    for _ in range(40):
        if health_ok():
            print(f"常駐サーバー起動: http://localhost:{PORT}")
            subprocess.run(
                ["open", f"http://localhost:{PORT}"],
                check=False,
            )
            return
        time.sleep(0.5)

    error_log = LOG_DIR / "streamlit.err.log"
    details = ""
    if error_log.exists():
        details = "\n" + error_log.read_text(
            encoding="utf-8",
            errors="replace",
        )[-3000:]
    raise RuntimeError(
        "常駐サーバーが時間内に起動しませんでした。"
        f"ログ: {error_log}{details}"
    )


def stop() -> None:
    bootout()
    print("常駐サーバーを停止しました")


def status() -> None:
    result = run(
        ["launchctl", "print", f"{domain()}/{LABEL}"],
        check=False,
        capture=True,
    )
    print("launchd: 登録済み" if result.returncode == 0 else "launchd: 未登録")
    print("HTTP: 正常" if health_ok() else "HTTP: 応答なし")
    print(f"URL: http://localhost:{PORT}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        nargs="?",
        choices=["install", "restart", "stop", "status"],
        default="install",
    )
    args = parser.parse_args()

    if args.action in {"install", "restart"}:
        install()
    elif args.action == "stop":
        stop()
    else:
        status()


if __name__ == "__main__":
    main()
