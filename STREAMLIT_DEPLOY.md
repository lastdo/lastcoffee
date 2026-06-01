# Streamlit Cloud deployment

入口檔案：

```text
streamlit_app.py
```

依賴檔案：

```text
requirements.txt
```

部署方式：

1. 把此專案推到 GitHub。
2. 到 Streamlit Community Cloud 建立新 app。
3. Repository 選這個專案。
4. Main file path 填：

```text
streamlit_app.py
```

5. App URL 選一個中性的名稱，例如：

```text
lastcoffee
coffee-census
audio-census
```

部署後網址會像：

```text
https://lastcoffee.streamlit.app
```

重要提醒：

- 目前版本會讀寫 `data/census.json`。
- Streamlit Community Cloud 的本機檔案不適合當長期資料庫。
- 真正公開收集前，建議把儲存層改成你股票專案熟悉的雲端 JSON、Google Sheet、Firestore 或其他外部儲存。
