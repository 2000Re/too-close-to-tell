# Too Close to Tell

YouTube チャンネル **Too Close to Tell**([@too-close-to-tell](https://www.youtube.com/@too-close-to-tell))の Shorts を毎日自動で作って投稿する。

美術館の収蔵品の写真を、何か分からないほどのどアップから映し、少しずつ引いて、3・2・1 のあと一気に全体まで引いて正体を見せる(選択肢なし。答えだけを出す)。

- 写真と作品の情報: メトロポリタン美術館 Collection API(キー不要)。`isPublicDomain` が true(CC0)の作品だけを使う
- **AI は使わない。** 答えは `catalog.py` の表、説明は美術館のデータを型にはめて作る(`describe.py`)
- 声: Google Cloud Text-to-Speech(en-US-Chirp3-HD-Charon、1.1倍速)

## 流れ(1本 約16〜19秒)

1. どアップ。「WHAT IS IT? / Guess before it zooms out!」「Can you tell yet?」。少しずつ引く(最初の幅の 2.3 倍まで)
2. 「Last chance to guess!」→ 3・2・1
3. 一気に引いて、答え(金色の帯)「It's a violin!」
4. 説明「An Italian violin by Antonio Stradivari, from 1693. That's over 330 years old!」と、作品名・作者・年・素材
5. 「What did you guess? Tell me in the comments!」

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

カテゴリ: バイオリン、ギター、リュート、マンドリン、トランペット、ホルン、太鼓、兜、甲冑、鎖かたびら、盾、籠手、懐中時計、置き時計、アストロラーベ、地球儀・天球儀、日時計、扇、鞍、靴、ティーポット、オウムガイの杯、嗅ぎたばこ入れ、錠前、あぶみ、拍車、チェスの駒、かご。直近8本に出たカテゴリは選ばない。

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
6. cron-job.org: `POST https://api.github.com/repos/2000Re/too-close-to-tell/actions/workflows/post.yml/dispatches`、本文 `{"ref":"main","inputs":{"scheduled":"true"}}`、ヘッダー `Authorization: Bearer <token>`・`Accept: application/vnd.github+json`

ウェブサイト(Settings → Pages → `main` / `/docs`):

- ホーム: https://2000re.github.io/too-close-to-tell/
- プライバシーポリシー: https://2000re.github.io/too-close-to-tell/privacy.html
- 利用規約: https://2000re.github.io/too-close-to-tell/terms.html

## 出典

- 写真と作品の情報: [The Metropolitan Museum of Art Open Access](https://www.metmuseum.org/about-the-met/policies-and-documents/open-access)(CC0)。美術館とは関係のないチャンネル
- フォント: Liberation Sans(SIL Open Font License)
