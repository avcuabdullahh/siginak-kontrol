name: Build Siginak APK

on:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-java@v5
        with:
          distribution: zulu
          java-version: '17'

      - uses: actions/setup-python@v6
        with:
          python-version: '3.11'

      - name: Flutter Kur
        run: |
          git clone https://github.com/flutter/flutter.git --depth 1 -b stable $HOME/flutter
          echo "$HOME/flutter/bin" >> $GITHUB_PATH

      - name: Paketleri Kur
        run: |
          python -m pip install --upgrade pip
          pip install flet fpdf

      - name: APK Derle
        run: flet build apk

      - uses: actions/upload-artifact@v5
        with:
          name: siginak-kontrol-apk
          path: build/apk/
