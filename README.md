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
6. cron-job.org: `POST https://api.github.com/repos/2000Re/too-close-to-tell/actions/workflows/post.yml/dispatches`、本文 `{"ref":"main","inputs":{"scheduled":"true"}}`、ヘッダー `Authorization: Bearer <token>`・`Accept: application/vnd.github+json`。時刻は毎日 16:08・19:08 JST、取りこぼし用に30分後の 16:38・19:38(`08,38 16,19 * * *`。2026-11-22 に 16:41・19:41 から変更。先の回が成功していれば、予備の回は posted_today.py が止める)。2026-11-17 に 21:41 から 19:41 に変更(21時台の3本の平均 106回に対し、19時台は 404回だったため)

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

## 短くした(2026-11-21〜)

平均視聴割合(YouTube Analytics)が、Wait, That Big? の 90% 台に対して、このチャンネルは 56〜73% だった。
答えのあとの説明(「An Italian violin by …, from 1693. That's over 330 years old!」)の読み上げで離れる人が多いとみて、
読み上げはやめて画面に出すだけにした(`video.READ_SEC` 秒以上読めるようにする)。100年以上前の物は、
「Over 330 years old!」を答えの上に大きく出す(`describe.texts` の `age_line`)。15〜24秒 → 約13〜15秒。
投稿記録の `ending` は `short_quiet`(それまでの `short_tail` と、`stats.md` で比べられる)。

## 昔の台所・家事の道具の回(2026-11-21〜)

番号が4の倍数の回(`catalog.KITCHEN_EVERY`)は、昔の台所・家事の道具(`catalog.KITCHEN`)から出す。
どアップだと何に使うか分からない、見た目と用途のギャップを楽しむ回。長さはふつうの回と同じ。

- 道具: パイの縁切り(jagging wheel)・ナツメグおろし・コルク抜き・角砂糖ばさみ・乳鉢と乳棒・骨髄用スプーン・
  鍋敷き・暖炉で使ったパン焼き器(toaster)。メトロポリタン美術館の作品名(objectName)がその道具のものだけ
  (乳鉢は「mortar and pestle」と書かれたものだけ)。ほとんどが 1700〜1800 年代
- 問いは「This old everyday tool looks strange up close. What is it?」など、最後は「Would you still use this today?」など。
  「台所で使った」「貴族が〜」のような、美術館のデータで確かめられないことは言わない(年代・素材・国はデータから)
- 外れの選択肢は台所の道具以外から選ぶ。骨髄用スプーンと「A spoon」、パイの縁切りと「A pair of scissors」は並べない
- 台所の道具は検索結果のうち当てはまる物が少ないので、検索結果の順番のまま調べる(ほかのカテゴリはばらばらに)
- 題名は `make_short.KITCHEN_TITLES` の3種類。投稿記録の `format` は `kitchen`(ふつうの回は `object`)で、
  `stats.md` で比べられる
- ヴィクトリア朝のギア付きの器具(リンゴの皮むき器など)は Met にないので入れていない
  (スミソニアンのオープンデータを足せば出せる。API キーと作品ごとの CC0 の確認が要る)

## 再生リスト(2026-11-22〜、`playlists.py`・`playlist_rules.py`)

投稿するたびに、合う再生リストへ自動で入れる(なければ公開で作る)。どの再生リストに入れるかは `playlist_rules.py`。
`python playlists.py --show` で、これまでの回がどこに入るかを確かめられる(通信なし)。

- 再生リストの操作には、リフレッシュトークンに `youtube` スコープが要る(`get_youtube_refresh_token.py` に追加済み)。
  権限のないトークンのままでも投稿は止まらず、ログに警告が出るだけ
- 取り直し: Google Cloud Console の OAuth 同意画面(データアクセス)に `.../auth/youtube` を足してから、
  `python get_youtube_refresh_token.py client_secret.json` を実行し、Secrets の `YT_REFRESH_TOKEN` を新しい値にする
- これまでの動画は、Actions の「playlists」を手動で1回動かすとまとめて入る(入っている動画は入れ直さない)
- `playlists.py` と `.github/workflows/playlists.yml` は4チャンネルで同じファイル(`sync_check.py` で確かめる)

## 通常動画「10 Mystery Objects」(2026-11-23〜、`longform.py`)

横長(1920x1080)、10問・約3分、週1本(毎週木曜 10:13 UTC ごろ。`LONGFORM_AUTO` が `true` のときだけ)。
右に美術館の写真(どアップから少しずつ引く)、左の帯に問題・3択・5秒のカウントダウン。答えで全体まで引いて、
作品名・作り手と年代・何年前か(どれも美術館のデータから)。最後に10点を並べる。

- カテゴリは重ならない10種類: 身近な物7、昔の道具2まで、残りはそれ以外。似た物(楽器どうしなど)は1つだけ
- Shorts と過去の通常動画で使った作品は使わない。Shorts も通常動画で使った作品を選ばない
- チャプターは「Object 1」などにして、答えは書かない。答えは説明欄の下の方にまとめる
- サムネイル a・b・c、再生リスト「10 Mystery Objects: Full Quizzes」、Shorts の説明欄のリンクは他のチャンネルと同じ
- Met の写真は1点ずつ取って、どアップに向くか確かめる(`make_short.find`)ので、作るのに時間がかかる(最大75分)

## 投稿時刻(2026-11-24〜)

4チャンネルで1日8本を3時間おきに割り振った(各チャンネルの2本は12時間離す。予備は30分後。タイムゾーン Asia/Tokyo):

| チャンネル | 投稿 | cron 式 |
|---|---|---|
| Painted When? | 0:17・12:17 | `17,47 0,12 * * *` |
| Too Close to Tell | 3:08・15:08 | `08,38 3,15 * * *` |
| Guess From Space | 6:04・18:04 | `04,34 6,18 * * *` |
| Wait, That Big? | 9:23・21:23 | `23,53 9,21 * * *` |

(2026-11-24 に、上の表から1時間ずつ早めた。以前は 1:17・4:08・7:04・10:23 からの3時間おき)

上に書かれた以前の時刻は経緯として残している。先の回が成功していれば、予備の回は posted_today.py が止める。

## 通常動画の予告編の Short(2026-11-24〜、`make_short.teaser_plan`)

通常動画(10 Mystery Objects)を投稿してから3日以内の最初の Shorts の回を、その通常動画の予告編にする(週1本。本数は増やさない)。
Wait, That Big? と同じ仕組み。

- 通常動画の問題から1問(最初の2問と、Shorts に出したものは避ける)を、いつもの Shorts と同じ形で答えまで見せる
- 最後の約2秒、上に「Object 3 of 10 · 10 Mystery Objects #1 / Play all 10 objects!」の帯を重ね、最後の一言は「That was object N. Want M more? Tap the link to play the full challenge!」
- 説明欄の1行目に通常動画のリンク。投稿記録の `teaser` に通常動画の番号が入る(同じ回の予告編は1本だけ)
- **YouTube Studio で、その Short の「関連動画」に通常動画を設定する**(API ではできない。画面にタップできるリンクが出る)

## 通常動画の予約投稿(2026-11-24〜、`longform.scheduled_publish`)

2026-11-26 から、作るのを前日の水曜 10:13 UTC(19:13 JST)ごろに早めた(11/25 の Painted When? #2 は、定期実行が8時間半遅れて予約の20分前にやっと上がったため)。公開は今までどおり当日 19:13 JST。

GitHub の定期実行は数時間遅れることがあるので、通常動画は木曜 1:13 UTC(10:13 JST)ごろに作って非公開で上げ、
木曜 19:13 JST に YouTube が公開する(YouTube Data API の `publishAt`)。

- 定期実行が遅れて、公開の時刻の10分前を過ぎていたら、すぐ公開する。日付をまたいで遅れたときも、来週にはせずすぐ公開する
- 投稿記録(`longform_history.json`)の `publish_at` に公開の時刻が入る。Shorts の説明欄のリンクと予告編の Short は、
  公開の時刻を過ぎてから(公開前の動画を案内しない)
- 手動実行は今までどおり、選んだ公開設定ですぐ上げる(予約しない)

通常動画の公開は、2026-11-28 から木曜 8:13 JST(アメリカ東部の前日の夜 18:13)。作るのは前日の水曜 1:13 UTC(10:13 JST)ごろ。

題名と説明の翻訳(日本語・スペイン語・フランス語・ドイツ語・ポルトガル語)は locales.py(2026-11-28 から。ほかの3チャンネルと同じ仕組み。AI は使わない)。
