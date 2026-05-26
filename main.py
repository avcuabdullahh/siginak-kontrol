name: Build Siginak APK

on:
  workflow_dispatch:

env:
  ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION: true

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          distribution: zulu
          java-version: '17'

      - uses: actions/setup-python@v5
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

      - uses: actions/upload-artifact@v4
        with:
          name: siginak-kontrol-apk
          path: build/apk/
