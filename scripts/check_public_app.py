from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request


DEFAULT_URL = "https://teeqy5f9waeoacgwccu4yc.streamlit.app"


def get(url: str, timeout: float) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "regional-map-app-healthcheck/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read(200_000)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--attempts", type=int, default=12)
    parser.add_argument("--interval", type=float, default=10)
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args()

    root = args.url.rstrip("/")
    last_error = None

    for attempt in range(1, args.attempts + 1):
        print(f"[{attempt}/{args.attempts}] 公開版を確認")
        try:
            health_status, health_body = get(
                root + "/_stcore/health",
                args.timeout,
            )
            page_status, page_body = get(root, args.timeout)

            health_text = health_body.decode(
                "utf-8",
                errors="replace",
            ).strip().lower()
            page_text = page_body.decode(
                "utf-8",
                errors="replace",
            ).lower()

            if (
                health_status == 200
                and health_text in {"ok", "healthy"}
                and page_status == 200
                and "streamlit" in page_text
            ):
                print("公開版: OK")
                print(f"- URL: {root}")
                return

            last_error = RuntimeError(
                f"health={health_status}:{health_text}, "
                f"page={page_status}"
            )
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error

        if attempt < args.attempts:
            time.sleep(args.interval)

    raise SystemExit(f"公開版の確認に失敗: {last_error}")


if __name__ == "__main__":
    main()
