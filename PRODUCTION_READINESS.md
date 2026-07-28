# Production Readiness

## 提出前

```bash
source .venv/bin/activate
python scripts/quality_gate.py
```

確認内容：

- 依存関係の衝突
- Python構文
- データの件数・重複・計算式
- 全単体テスト
- Streamlitのヘッドレス実行
- 実行時例外
- 主要タブの描画
- 初回実行90秒以内

## 公開版

```bash
python scripts/check_public_app.py
```

Streamlit Community Cloudがスリープ中でも、10秒間隔で最大12回確認する。

## GitHub Actions

`.github/workflows/production-quality.yml`は、mainへのpush、Pull Request、手動実行で品質ゲートを動かす。
