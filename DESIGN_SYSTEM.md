# Design System

## 目的

画面ごとにCSSを足し続けるのではなく、共通スタイルを`assets/app.css`へ集約する。  
見た目の調整とPythonの処理を分け、変更箇所を追いやすくする。

## ファイル

- `assets/app.css`：アプリ全体のスタイル
- `ui_theme.py`：CSSの読込
- `app.py`：データ処理と画面構成
- `population_factors_tab.py`：要因分析
- `guided_demo_tab.py`：3分デモ
- `project_portfolio_tab.py`：プロジェクト説明

## 方針

### 色

- 本文：濃い青灰色
- 背景：薄い青灰色
- 紙面：白
- 主な差し色：くすんだ青
- 補助色：茶、青紫

色だけで状態を伝えず、文字、線、太さを併用する。

### 角と影

- 角丸は小〜中程度
- 影は情報の階層を作る範囲だけ
- すべてのカードを同じ見た目にしない

### 文章

- 見出しは短く
- 本文は常体
- ボタンは押した後の動作を書く
- 相関、分類、色の意味は簡潔に注記する

### アクセシビリティ

- キーボードフォーカスを表示
- タブを横スクロール可能にする
- `prefers-reduced-motion`へ対応
- 高コントラストモードへ対応
- 白背景上の本文は十分に濃くする

## CSSを変更するとき

1. `assets/app.css`を編集
2. `python -m unittest discover -s tests -v`
3. `python scripts/install_local_service.py restart`
4. localhostでデスクトップ幅と狭い幅を確認
