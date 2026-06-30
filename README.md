# DoMySubs - סטודיו כתוביות לעברית

מערכת להפקת כתוביות בפורמט SRT בעברית מכל שפה — מבוססת על [WhisperX](https://github.com/m-bain/whisperX).

## יכולות

- **וידאו / אודיו** — תמלול אוטומטי + תרגום לעברית
- **יוטיוב** — הורדה, תמלול ותרגום בלחיצה אחת
- **SRT קיים** — תרגום כתוביות משפה אחרת לעברית (שומר על טיימסטמפים)
- **ממשק סטודיו** — ממשק Gradio נוח בדפדפן
- **CLI** — שימוש משורת הפקודה

## דרישות מערכת

1. **Python 3.10+**
2. **ffmpeg** — [הורדה](https://ffmpeg.org/download.html) והוספה ל-PATH
3. **yt-dlp** — להורדות מיוטיוב (מותקן אוטומטית עם pip)
4. **GPU (אופציונלי)** — CUDA 12.8 לתמלול מהיר

## התקנה

```bash
cd DoMySubs
pip install -r requirements.txt
```

או להתקנה כחבילה:

```bash
pip install -e .
```

העתק את `.env.example` ל-`.env` והתאם הגדרות:

```bash
copy .env.example .env
```

## הפעלה

### סטודיו (ממשק גרפי)

```bash
python -m domysubs.studio
```

פתח בדפדפן: http://127.0.0.1:7860

### שורת פקודה

```bash
# וידאו / אודיו
python -m domysubs "video.mp4"

# יוטיוב
python -m domysubs "https://www.youtube.com/watch?v=..."

# תרגום SRT קיים
python -m domysubs subtitles_en.srt --srt-only

# עם הגדרות
python -m domysubs video.mp4 --language en --model large-v2 --device cuda
```

## זרימת עבודה

```
קלט (וידאו / אודיו / יוטיוב / SRT)
        │
        ▼
┌───────────────────┐
│  חילוץ אודיו      │  ← ffmpeg (לוידאו)
│  / הורדת יוטיוב   │  ← yt-dlp
└─────────┬─────────┘
          ▼
┌───────────────────┐
│  תמלול WhisperX   │  ← זיהוי שפה + טיימסטמפים מדויקים
└─────────┬─────────┘
          ▼
┌───────────────────┐
│  תרגום לעברית     │  ← Google Translate
└─────────┬─────────┘
          ▼
     קובץ SRT בעברית
```

## קבצי פלט

נשמרים ב-`workspace/output/`:

```
subtitles_he_20260629_143022.srt
translated_he_20260629_143500.srt
```

## הגדרות (.env)

| משתנה | ברירת מחדל | תיאור |
|--------|------------|--------|
| `DOMYSUBS_DEVICE` | `cpu` | `cpu` או `cuda` |
| `DOMYSUBS_MODEL` | `large-v2` | מודל Whisper |
| `DOMYSUBS_BATCH_SIZE` | `8` | הקטן אם חסר זיכרון |
| `DOMYSUBS_COMPUTE_TYPE` | `int8` | `int8` ל-CPU, `float16` ל-GPU |
| `DOMYSUBS_AUTO_SCAN` | `true` | סריקת חומרה אוטומטית בפתיחת הסטודיו |

## עיבוד תיקייה (אצווה)

עיבוד גורף של כל הסרטונים בתיקייה — כל SRT באותו שם כמו הוידאו + Excel מסודר.

**בסטודיו:** טאב «תיקייה (אצווה)»

**בשורת פקודה:**
```bash
python -m domysubs --batch-folder "C:\Videos\MyFolder"
python -m domysubs --batch-folder "C:\Videos" -o "C:\Videos\subtitles_he"
```

**פלט:**
```
MyFolder/DoMySubs_output/20260629_143022/
├── video1.srt
├── video2.srt
├── manifest.xlsx    ← שם וידאו | שם SRT | מיקום | סטטוס
└── כתוביות_מאוגדות.zip
```

---

## סנכרון עם GitHub

### העלאה ראשונית (פעם אחת)

```bash
# התחברות ל-GitHub
gh auth login

# יצירת repo והעלאה
cd DoMySubs
git branch -M main
gh repo create DoMySubs --public --source=. --remote=origin --push
```

### עדכון שינויים מקומיים → GitHub

```bash
cd DoMySubs
git add .
git commit -m "תיאור השינוי"
git push
```

### עדכון ב-Colab מ-GitHub

במקום ZIP, הרץ בתא Colab:

```python
import os
os.chdir('/content/DoMySubs')
!git pull
```

או שכפול ראשוני:

```python
!git clone https://github.com/YMTzioni/DoMySubs.git /content/DoMySubs
```

---

## סריקת חומרה

המערכת יכולה לזהות את המחשב שלך ולהתאים הגדרות אוטומטית:

**בסטודיו:** לחץ «סרוק חומרה והתאם הגדרות» (גם רץ אוטומטית בפתיחה).

**בשורת פקודה:**
```bash
python -m domysubs --scan-hardware
```

הסריקה בודקת: CPU, RAM, GPU/CUDA, VRAM, ffmpeg, yt-dlp — וממליצה על מכשיר, מודל, batch size ו-compute type.

## הערות

- **תרגום** משתמש ב-Google Translate (חינמי, דורש אינטרנט). איכות התרגום תלויה בשירות.
- **תמלול עברית** — WhisperX תומך ביישור (alignment) לעברית.
- **מודלים גדולים** (`large-v2`) מדויקים יותר אך איטיים יותר על CPU.
- לוידאו ארוך על CPU, שקול `--model medium` או `small` לזמן עיבוד סביר.

## רישיון

פרויקט זה משתמש ב-WhisperX (BSD-2-Clause) ובספריות קוד פתוח נוספות.
