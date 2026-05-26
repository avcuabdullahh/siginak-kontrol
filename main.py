name: Build Siginak APK

on:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Java
        uses: actions/setup-java@v4
        with:
          distribution: zulu
          java-version: '17'

      - name: Python
        uses: actions/setup-python@v6
        with:
          python-version: '3.11'

      - name: Flutter Kur
        run: |
          git clone https://github.com/flutter/flutter.git --depth 1 -b stable $HOME/flutter
          echo "$HOME/flutter/bin" >> $GITHUB_PATH

      - name: Paketler
        run: |
          python -m pip install --upgrade pip
          pip install flet fpdf

      - name: APK Derle
        run: flet build apk

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: siginak-kontrol-apk
          path: build/apk/
