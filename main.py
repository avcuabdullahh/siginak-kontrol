name: Build Siginak APK

on:
  workflow_dispatch:

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true
ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true
jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Repo Checkout
        uses: actions/checkout@v4

      - name: Java 17 Kur
        uses: actions/setup-java@v4
        with:
          distribution: zulu
          java-version: '17'

      - name: Python Kur
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Flutter Manuel Kurulum
        run: |
          git clone https://github.com/flutter/flutter.git --depth 1 -b stable $HOME/flutter
          echo "$HOME/flutter/bin" >> $GITHUB_PATH

      - name: Flutter Kontrol
        run: flutter doctor

      - name: Flet Kur
        run: |
          python -m pip install --upgrade pip
          pip install flet fpdf

      - name: APK Derle
        run: flet build apk

      - name: APK Upload
        uses: actions/upload-artifact@v4
        with:
          name: siginak-kontrol-apk
          path: build/apk/
