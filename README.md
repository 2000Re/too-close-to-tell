# Too Close to Tell

YouTube チャンネル **Too Close to Tell**([@too-close-to-tell](https://www.youtube.com/@too-close-to-tell))の Shorts を毎日自動で作って投稿する。

美術館の収蔵品の写真を、何か分からないほどのどアップから映し、少しずつ引いて、3・2・1 のあと一気に全体まで引いて正体を見せる 3択クイズ(#10 から。#9 までは選択肢なしで答えだけを出していた)。
外れの選択肢は、ほかのカテゴリの答えから選ぶ(`catalog.choices_for`。どアップで見分けにくい仲間同士(弦楽器、武具、時計など、`GROUPS`)は同じ回に並べない。AI は使わない)。

- 写真と作品の情報: メトロポリタン美術館 Collection API(キー不要)。`isPublicDomain` が true(CC0)の作品だけを使う
- **AI は使わない。** 答えは `catalog.py` の表、説明は美術館のデータを型にはめて作る(`describe.py`)
- 声: Google Cloud Text-to-Speech(en-US-Chirp3-HD-Charon、1.1倍速)

## 流れ(1本 約16〜19秒)

1. どアップ。「WHAT IS IT? / Guess before it zooms out!」と3択(例「A trumpet, a helmet, or a teapot?」)。少しずつ引く(最初の幅の 2.3 倍まで)
2. 「Lock in your answer!」→ 3・2・1
3. 一気に引いて、答え(金色の帯)「It's a violin!」
4. 説明「An Italian violin by Antonio Stradivari, from 1693. That's over 330 years old!」と、作品名・作者・年・素材
5. 「Did you get it right? Tell me in the comments!」

## ファイル

| ファイル | 役割 |
|---|---|
| `make_short.py` | カテゴリと作品を選び、動画(`out/video.mp4`)と `out/meta.json` を作る |
| `catalog.py` | カテゴリの表(検索語、作品名の条件、答え)。扱わない物(宗教・儀式の物、人の骨など、象牙) |
| `met.py` | 美術館の API(1秒5回まで) |
| `spot.py` | どアップにする場所を写真から自動で選ぶ(無地の背景から物を切り出し、輪郭が写らず模様が細かい場所)。小さい・ぼけた・背景が無地でない写真は使わない |
| `describe.py` | 答え・読み上げ・画面の説明を、データから型にはめて作る |
| `video.py` | 動画の組み立て |
| `media.py` | 文字・ボタン・TTS・効果音・ffmpeg |
| `youtube_upload.py` | アップロードと `upload_history.json` への記録(`YT_CHANNEL_ID` 必須。違うチャンネルなら中止) |
| `posted_today.py` | 定期実行で、今日もう投稿したかを調べる(1日2本、前の投稿から1.5時間) |
| `get_youtube_refresh_token.py` | リフレッシュトークンの取得(ローカルPCで一度だけ) |
| `docs/` | GitHub Pages(ホーム・プライバシーポリシー・利用規約) |

カテゴリ: バイオリン、ギター、リュート、マンドリン、トランペット、ホルン、太鼓、兜、甲冑、鎖かたびら、盾、籠手、懐中時計、置き時計、アストロラーベ、地球儀・天球儀、日時計、扇、鞍、靴、ティーポット、オウムガイの杯、嗅ぎたばこ入れ、錠前、あぶみ、拍車、チェスの駒、かご、スプーン、カップ、はさみ、燭台、帽子、瓶。直近8本に出たカテゴリは選ばない。

**身近な物を中心に出す**(2026-11-17〜): 85%(`catalog.EVERYDAY_SHARE`)は今の暮らしで見かける物(`catalog.EVERYDAY`:
靴・ティーポット・時計・楽器・スプーン・カップ・はさみ・燭台・帽子・瓶など)から、残りは武具・古い楽器・天文の道具などから選ぶ。
2026-11-17 の `stats.md` で、靴(422)が兜・盾・角笛(66〜108)の3倍以上見られていたため。
スプーン・カップ・はさみ・燭台・帽子・瓶はこのとき追加した(呼び鈴は使える写真が見つからず見送り)。

## 手元で試す

```bash
pip install -r requirements.txt     # ほかに ffmpeg が必要
python make_short.py --tts dummy --history /tmp/none.json --out /tmp/tctt
python make_short.py --tts dummy --category violin --object 503045 --history /tmp/none.json --out /tmp/tctt
```

## 自動投稿のセットアップ

Wait, That Big? と同じ手順(チャンネルは同じ Google アカウントのブランドアカウント、GCP プロジェクトとリポジトリは別)。

1. GCP プロジェクト `too-close-to-tell` を作り、YouTube Data API v3 と Cloud Text-to-Speech API を有効にする
2. OAuth 同意画面(外部・本番環境)。アプリ名「Too Close to Tell Uploader」。ホームページ・プライバシーポリシー・利用規約に下の URL、承認済みドメイン `2000re.github.io`。スコープ `youtube.upload` と `youtube.readonly`
3. OAuth クライアント(デスクトップアプリ)→ JSON → ローカルで `python get_youtube_refresh_token.py client_secret_xxx.json`。**チャンネルの選択で Too Close to Tell を選ぶ**
4. Text-to-Speech の API キー(Cloud Text-to-Speech API だけに制限)
5. Secrets: `YT_CLIENT_ID`、`YT_CLIENT_SECRET`、`YT_REFRESH_TOKEN`、`YT_CHANNEL_ID`、`GOOGLE_TTS_API_KEY`。Variables: `AUTO_POST` = `true`
6. cron-job.org: `POST https://api.github.com/repos/2000Re/too-close-to-tell/actions/workflows/post.yml/dispatches`、本文 `{"ref":"main","inputs":{"scheduled":"true"}}`、ヘッダー `Authorization: Bearer <token>`・`Accept: application/vnd.github+json`。時刻は毎日 16:41・19:41 JST(`41 16,19 * * *`)。2026-11-17 に 21:41 から 19:41 に変更(21時台の3本の平均 106回に対し、19時台は 404回だったため)

ウェブサイト(Settings → Pages → `main` / `/docs`):

- ホーム: https://2000re.github.io/too-close-to-tell/
- プライバシーポリシー: https://2000re.github.io/too-close-to-tell/privacy.html
- 利用規約: https://2000re.github.io/too-close-to-tell/terms.html

## 出典

- 写真と作品の情報: [The Metropolitan Museum of Art Open Access](https://www.metmuseum.org/about-the-met/policies-and-documents/open-access)(CC0)。美術館とは関係のないチャンネル
- フォント: Liberation Sans(SIL Open Font License)

## 毎日の確認(`.github/workflows/daily-check.yml`)

毎日 03:29 JST ごろ(GitHub の schedule なので遅れることがある)に動く。手動では Actions → daily-check → Run workflow。

- **投稿が止まっていないか**(`watchdog.py`): 最後の投稿から30時間以上たっていたら Issue(ラベル `post-stalled`)を立てる。
  cron-job.org のトークン切れなどで post が起動されなかったときは post.yml 自身では何も残らないので、その見張り。
  投稿が再開すると次の確認で自動で閉じる。変数 `AUTO_POST` が `true` でないときは調べない
- **再生数の記録**(`stats.py`): 全動画の再生数・高評価・コメント数を YouTube Data API で取り、`stats.json` に残す。
  比べやすいよう、投稿から1日・3日・7日の時点の値を固定して残す(この仕組みより前の動画は最新の値だけ)。
  `stats.md` に、`upload_history.json` の項目(題名の型・版・カテゴリ・形式・美術館など、あるもの)と投稿の時間帯ごとの
  3日目の再生数の平均・中央値をまとめる。使う Secrets は投稿と同じ(`YT_CLIENT_ID`・`YT_CLIENT_SECRET`・`YT_REFRESH_TOKEN`)
- **共通ファイルのずれ**(`sync_check.py`): 4つのリポジトリの main を読み比べ、同じであるべきファイル
  (`stats.py`・`watchdog.py`・`sync_check.py`・`daily-check.yml`)が違えば sync ジョブを失敗にする。
  似ているファイル(`youtube_upload.py`・`posted_today.py` など)は、違う行数を Summary に並べる。
  1つで不具合を直したら、ほかの3つにも同じ直しが要るかを見る。中身は `python sync_check.py --diff youtube_upload.py`
- `stats.py`・`watchdog.py`・`sync_check.py` は4チャンネル(Painted When?、Guess From Space、Wait, That Big?、Too Close to Tell)で同じファイル

## YouTube Analytics の数字(2026-11-21〜、`stats.py`)

`stats.md` に、動画ごとの平均視聴割合・登録者の増加と、日別の流入元(ショート フィードからの再生の割合)も出すようにした
(YouTube Analytics API。数字は2〜3日遅れ)。使うには、次の作業が1回だけ要る。それまでは、この部分だけ飛ばして今までどおり動く。

1. Google Cloud Console(このチャンネルのプロジェクト)で、「API とサービス」→「ライブラリ」→ **YouTube Analytics API** を有効にする
2. OAuth 同意画面の「データアクセス」に、スコープ `https://www.googleapis.com/auth/yt-analytics.readonly` を追加する
3. ローカル PC で `python3 get_youtube_refresh_token.py client_secret_xxx.json` を実行し直す(スコープに yt-analytics.readonly が加わった)
4. 表示された `YT_REFRESH_TOKEN` で、GitHub の Secrets を更新する(ほかの値は変わらない)

## 最後の終わり方(2026-11-21〜)

Shorts は最後まで見られると頭からくり返される。くり返し再生につなげやすいよう、最後の読み上げのあとの間を短くした
(Painted When?・Guess From Space は、最後に冒頭と同じ拡大した場面へ戻る)。どちらの終わり方かは
`upload_history.json` の `ending` に残り、`stats.md` で比べられる。

## 登録につなげる工夫(2026-11-21〜)

再生数は伸びているのに、高評価・コメント・登録がほとんどなかったので、次を入れた。

- 最後の一言を、答えをコメントしたくなる問いと、毎日続くシリーズだと伝える一言にした(`video.LINES["outro"]`。
  例: 「What did you guess? Follow for a new mystery object every day!」)
- 説明欄に「What did you guess? Tell me in the comments!」「Follow for a new mystery object every day.」と、
  姉妹チャンネル(Wait, That Big?・Painted When?・Guess From Space)へのリンク(`make_short.SISTERS`)
- ほかの3チャンネルの説明欄からも、このチャンネルへリンクする
