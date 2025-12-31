# 🏷️ נקודת שמירה בגיט

נוצר tag בשם `checkpoint-20251231-011858`.
בריפו: `amirbiron/AI-Tools`

כך ניתן לשחזר לאותה נקודה במחשב המקומי:

1. עדכן תגיות מהריפו:

```bash
git fetch --tags
```

2. מעבר לקריאה בלבד ל-tag (מצב detached):

```bash
git checkout tags/checkpoint-20251231-011858
```

3. לחזרה לענף הראשי לאחר מכן:

```bash
git checkout -
```

> הערות:
> - נקודת שמירה היא רפרנס ל-commit (tag או branch).
> - ניתן למחוק את הקובץ הזה לאחר השחזור.
