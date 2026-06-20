name: Daily News Post

on:
  schedule:
    # Saare times IST (India) ke hisaab se hain, UTC mein convert kiye gaye:
    - cron: "30 0 * * *"   # 6:00 AM IST
    - cron: "30 4 * * *"   # 10:00 AM IST
    - cron: "30 11 * * *"  # 5:00 PM IST
    - cron: "30 14 * * *"  # 8:00 PM IST
  workflow_dispatch: {}     # Manual "Run workflow" button ke liye, testing mein useful

jobs:
  post:
    runs-on: ubuntu-latest
    permissions:
      contents: write   # repo mein generated images push karne ke liye chahiye

    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Dependencies install karo
        run: pip install -r requirements.txt

      - name: News carousel generate karo
        env:
          NEWS_API_KEY: ${{ secrets.NEWS_API_KEY }}
          UNSPLASH_ACCESS_KEY: ${{ secrets.UNSPLASH_ACCESS_KEY }}
        run: |
          python3 -c "
          import sys, json
          sys.path.insert(0, 'scripts')
          from fetch_news import fetch_top_headlines, NewsFetchError
          from generate_news_post import generate_carousel

          with open('state.json') as f:
              state = json.load(f)
          already_posted = set(state.get('posted_headline_hashes', []))

          try:
              headlines = fetch_top_headlines(already_posted)
          except NewsFetchError as e:
              print(f'FETCH_ERROR::{e}')
              sys.exit(1)

          if not headlines:
              print('NO_FRESH_HEADLINES')
              # 'skip' file banao taaki next steps pata kar saken post nahi karna
              with open('.skip_post', 'w') as f:
                  f.write('1')
              sys.exit(0)

          meta = generate_carousel(headlines)
          # meta ko temp file mein save karo taaki run_news_daily.py
          # dobara fetch kiye bina seedha isi se Instagram pe post kar sake
          with open('.carousel_meta.json', 'w', encoding='utf-8') as f:
              json.dump(meta, f, ensure_ascii=False)
          print('GENERATED_OK')
          "

      - name: Generated images ko commit aur push karo
        if: hashFiles('.skip_post') == ''
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add posts/
          git diff --staged --quiet || git commit -m "Daily news carousel: $(date -u +'%Y-%m-%d %H:%M UTC')"
          git push

      - name: Instagram pe post karo + Telegram notify karo
        if: hashFiles('.skip_post') == ''
        env:
          NEWS_IG_USER_ID: ${{ secrets.NEWS_IG_USER_ID }}
          NEWS_IG_ACCESS_TOKEN: ${{ secrets.NEWS_IG_ACCESS_TOKEN }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_BRANCH: ${{ github.ref_name }}
        run: python3 scripts/run_news_daily.py

      - name: Koi fresh headline na milne par Telegram bata do
        if: hashFiles('.skip_post') != ''
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          python3 -c "
          import sys
          sys.path.insert(0, 'scripts')
          from telegram_utils import send_telegram_message
          import os
          send_telegram_message(
              os.environ.get('TELEGRAM_BOT_TOKEN'),
              os.environ.get('TELEGRAM_CHAT_ID'),
              'ℹ️ Is baar koi nayi headline nahi mili, news post skip ho gaya.'
          )
          "
