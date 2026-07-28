# Runbook

## 公開版

公開版はStreamlit Community Cloud上で動作します。GitHubの`main`へpushすると自動更新されます。

- 公開URL: https://teeqy5f9waeoacgwccu4yc.streamlit.app
- ターミナルを閉じても公開版は停止しません。

## Mac内の確認用サーバー

macOSの`launchd`へ登録しているため、ターミナルを閉じても`http://localhost:8501`は動作します。ログイン時に自動起動し、異常終了時は再起動します。

### 状態確認

```bash
python scripts/install_local_service.py status
```

### 再起動

```bash
python scripts/install_local_service.py restart
```

### 停止

```bash
python scripts/install_local_service.py stop
```

### 再登録

```bash
python scripts/install_local_service.py install
```

## ログ

- `.logs/streamlit.out.log`
- `.logs/streamlit.err.log`

## 注意

`localhost`はこのMacだけで見るためのURLです。Macの電源が切れている間は利用できません。外部へ提出・共有するときは公開URLを使用します。
