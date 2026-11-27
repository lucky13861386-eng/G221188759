# Pixabay 素材串接

Pixabay 是免費的照片／影片素材庫。這份說明教你怎麼用 `scripts/pixabay.py` 把素材抓下來，當成實拍 B-roll（全螢幕畫面或背景）。

> 什麼時候用：主題需要**真實畫面**（海浪、森林、城市、食物、運動…），用 HTML 動畫畫不出來、或畫出來不如實拍自然時。概念圖、數字、剖面這類還是用 Hyperframes 動畫（見 `design-system.md`、`cross-section.md`）。

---

## 1. 先申請一把免費金鑰（只要做一次）

1. 到 https://pixabay.com 註冊並登入（免費）。
2. 登入後打開 https://pixabay.com/api/docs/ ，頁面上會顯示**你的 API key**（一串英數字）。
3. 把這串金鑰設定給工具用，三種方式擇一（**推薦第 1 種，最簡單**）：

   **方式 1：放進檔案（推薦給不想碰指令的人）**
   在 repo 最外層（和 `README.md` 同一層）建立一個檔案 `.pixabay-key`，把金鑰貼進去存檔。
   這個檔案已經設定**不會上傳到 GitHub**，金鑰不會外流。

   **方式 2：設環境變數**
   - Mac／Linux：`export PIXABAY_API_KEY=你的金鑰`（想每次自動生效就加到 `~/.zshrc` 或 `~/.bashrc`）
   - Windows PowerShell：`setx PIXABAY_API_KEY "你的金鑰"`（設定後重開終端機）

   **方式 3：臨時指定**
   每次指令後面加 `--key 你的金鑰`。缺點：金鑰會留在指令紀錄裡，不建議。

> ⚠️ 金鑰等於你的帳號密碼，**絕對不要**直接寫進任何會 commit 的檔案或分鏡表裡。

---

## 2. 搜尋素材

```bash
# 照片＋影片都搜（預設）
python3 .claude/skills/broll-video/scripts/pixabay.py search "睡眠 床"

# 只搜影片、直式（最適合 9:16 Reels）
python3 .claude/skills/broll-video/scripts/pixabay.py search "ocean waves" --type video --orientation vertical

# 只搜照片
python3 .claude/skills/broll-video/scripts/pixabay.py search "沙拉 蔬菜" --type photo
```

常用參數：

| 參數 | 作用 |
|---|---|
| `--type photo\|video\|all` | 要照片、影片、還是兩種都要（預設 all） |
| `--orientation vertical` | 只要直式，9:16 直接用不卡；`horizontal` 是橫式 |
| `--per-page 15` | 每種類型回傳幾筆（3–50） |
| `--editors-choice` | 只看 Pixabay 精選（品質通常比較穩） |
| `--safesearch` | 只回傳適合各年齡的素材 |

**小技巧：關鍵字用英文命中率通常高很多**（例：`sleep bed`、`ocean waves`、`salad vegetables`）。
搜尋結果會列出每筆的 `id`、尺寸、作者、預覽頁網址。先點預覽頁看合不合適，再記下 `id` 下載。

---

## 3. 下載到專案

照片和影片的 `id` 系統不同，所以**要分開下載**（`--type` 要對）：

```bash
# 下載照片（id 從 search 結果來，可以一次好幾個）
python3 .claude/skills/broll-video/scripts/pixabay.py fetch --type photo \
  --project projects/example-aspartame 1234567 2345678

# 下載影片
python3 .claude/skills/broll-video/scripts/pixabay.py fetch --type video \
  --project projects/example-aspartame 9876543
```

下載後：

- 素材檔放在 `projects/<專案>/inputs/broll/pixabay/`（**不進 Git**，用雲端硬碟傳給夥伴）。
  檔名格式：`pixabay-photo-<id>.jpg`、`pixabay-video-<id>.mp4`。
- 出處與授權自動寫進 `projects/<專案>/storyboard/pixabay-credits.md`（**會進 Git**，供備查）。
- 同一資料夾另有 `manifest.json`，記錄每個檔案對應的 Pixabay 頁面、作者、標籤。

影片畫質可用 `--size large|medium|small` 選（預設 large）。

---

## 4. 接進分鏡與製作流程

1. **分鏡（步驟 2）**：決定哪幾句要用實拍畫面時，在 `storyboard.md` 的「畫面描述」寫清楚用哪個素材
   （例：`背景＝pixabay-video-9876543.mp4（海浪，直式），上疊標題字`），並在「類型」標為「全」。
2. **放進 composition（步驟 4）**：把素材從 `inputs/broll/pixabay/` 複製或引用到 `composition/`，
   用 `<video>`／`<img>` 當某個 `<section class="clip scene">` 的背景層，再疊字幕／標題。
   - 影片素材屬於「`prepare-composition.py` 不會自動搬」的檔案，請自己複製進 `composition/` 並在 HTML 用相對路徑引用；
     `.gitignore` 已設定 `composition/*.mp4` 等不進 Git。
   - 直式 9:16 用 `object-fit: cover` 填滿 1080×1920；橫式素材會左右裁切，構圖重點要留在中間。
3. **品質檢查（步驟 6）**：實拍背景上的字要確認對比夠（必要時加半透明深色遮罩），不要被背景蓋掉。

---

## 5. 授權與 compliance（重要）

Pixabay 素材採 **Pixabay Content License**：

- ✅ 可免費使用、可商用、**不強制**註明出處（但我們仍用 `pixabay-credits.md` 內部備查）。
- ❌ 不可把素材**原樣**轉售或單獨再散布（例如做成另一個素材包去賣）。
- ⚠️ 素材若出現**可辨識的人物、商標、品牌、藝術作品、地標**，可能另有肖像權／商標限制，
  知識衛教題材尤其小心：**不要讓畫面暗示某個真人有某種疾病或狀況**。
- ⚠️ 遵守本專案 `references/compliance.md` 與 `brands/<品牌>/compliance.md`：
  - 不用製造焦慮、羞辱身材的畫面（身材對比、醜化特寫等）。
  - 畫面若配合數字／研究結論，那些**數字仍要列進 `sources.md`**；素材本身的出處列在 `pixabay-credits.md`。

授權全文：https://pixabay.com/service/license-summary/

---

## 6. 常見問題

- **「找不到金鑰」**：照第 1 節設定 `.pixabay-key` 或 `PIXABAY_API_KEY`。
- **「連不上 Pixabay」**：
  - 自己電腦上：檢查網路。
  - 在 Claude Code 雲端 session 跑：雲端網路預設會擋外部網站，要把 `pixabay.com` 加進環境的
    Allowed domains（session 標題列 → 雲端環境選單 → Edit → Network access）。本工具平常建議在自己電腦上跑。
- **「429 請求太頻繁」**：免費金鑰每分鐘約 100 次，稍等再試。
- **中文關鍵字搜不到**：改用英文關鍵字。
