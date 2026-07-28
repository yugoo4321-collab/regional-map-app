# Design Notes — 遊び心の入れ方

## 目的

分析の信頼性を崩さず、最初の数秒で「少し触ってみたい」と思える入口を作る。

## 参考にした考え方

- 短尺動画サービスのように、最初に短いフックを置き、カードを連続して読める構成
- 2026年のデザインで見られる、過度に均一な生成AI風の表現から離れ、わずかな傾き、紙のような質感、限定的な差し色を使う方向
- モーションは状態変化や注目箇所を伝える範囲に限定し、`prefers-reduced-motion`へ対応
- Streamlitの標準部品を壊さず、HTML/CSSは表示補助に限定

## 今回追加したもの

1. **今日の1区**  
   日付をもとに毎日1区を表示。更新頻度の演出ではなく、探索の入口として使用。

2. **数字のひっかかり**  
   「人口最大」と「人口密度最大」が異なることを短い文章で提示。

3. **3秒クイズ**  
   答えを段階的に開くことで、受け身ではなく一度考えてからデータを見る。

4. **区ガチャ**  
   見たい区が決まっていない利用者向けのランダム探索。選択結果は本編へ引き継ぐ。

5. **控えめな手触り**  
   わずかな傾き、点のパターン、角の不均一さ、限定した暖色を追加。全画面を派手にしない。

## コピーしなかったもの

TikTokなど特定サービスのロゴ、配色、操作画面、ブランド表現はコピーしていない。参考にしたのは「短時間で理解できるフック」「次を見たくなる連続性」「タップで段階的に情報を開く」という体験の考え方のみ。

## 参考資料

- Streamlit Custom Components: https://docs.streamlit.io/develop/concepts/custom-components/overview
- PIE Design System — Motion: https://pie.design/foundations/motion/
- Creative Bloq — 2026 graphic design trends: https://www.creativebloq.com/design/graphic-design/texture-warmth-and-tactile-rebellion-the-big-graphic-design-trends-for-2026
