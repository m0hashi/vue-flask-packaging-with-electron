# Vue-Flask Packaging with Electron

Vue, python(Flask), Electron を利用して,ローカル環境でファイルを操作する GUI アプリを作成します。

アプリは下記のシンプルな機能を持ちます。

- クライアント側でローカルの csv を指定して、サーバー側に絶対パスを POST で渡す
- サーバは受け取った絶対パスにある csv ファイルを読み取り、クライアントに json として返却
- クライアントは受け取った json ファイルをテーブル形式で表示

最終的に Electron で 1 つの実行ファイルを作成して、python や nodejs の事前インストールなしにツールが使える形にします。

# 動作確認

前提
python >= 3.7
nodejs >= 12.0

## 環境構築

アプリを動作させるための python と vue, electron の環境を用意します。

```sh
git clone

cd server
pip3 install virtualenv
virtualenv -p python3.7 .venv
source ./venv/bin/activate
pip install -r requirements.txt

cd ../client
npm install -g @vue/cli@4.3.1
npm install
cd ..
```

## 実行

Electron でサーバとクライアントをパッケージングする前に、それぞれのアプリが独立に実行できることを確認します。
ローカルフィアルの絶対パスを扱う都合上、クライアント側はブラウザではなく Electron 上で実行します。
(環境構築で electron-builder を導入することで、packages.json の scripts に electron:serve が追加されています。)

サーバサイドの実行

```sh
cd server
python app/app.py
```

クライアントの実行

```sh
cd cliend
npm run electron:serve
```

# Electron 化手順

上記の動作確認ができた後、Electron で実行ファイルを 1 つにまとめます。
Flask サーバ側のアプリを 1 つの実行ファイルにまとめ、クライアント起動時にその Flask サーバを子プロセスとして立ち上げる方針でパッケージングを行います。

## 環境構築

Vue と python で作成した Electron 化前のアプリを pre-electron ブランチに作成してあります。
この手順でパッケージ化できることを確認するため、そちらのブランチに切り替えて再度バッケージをインストール後、electron-builder をインストールします。


```sh
git checkout pre-electron
```

```sh
cd server
source ./venv/bin/activate
pip install -r requirements.txt

cd ../client
npm install
vue add electron-builder #Electron化用のパッケージ
cd ..
```

注意
npm install electron-builderとすると、Electron本体が入らなかったり、packages.jsonのscripotsが更新されなかったりするので注意

## pyhon

まず Flask で作成した API サーバを pyinstaller を利用して、実行形式にパッケージングします。
--onefile で app.py に関連するファイルを 1 つにまとめ、--hidden-import で app.py から見えないものの必要なファイルを追加します。
今回の設定では、--distpathDir で指定したディレクトリに実行形式のファイルが app という名前で作成されます。

```sh
cd server
source ./venv/bin/activate
pyinstaller app/app.py --onefile --hidden-import pkg_resources.py2_warn --distpathDir ../client/electron_build
cd ..
```

## Vue

Vue クライアントの側では、クライアント起動時に子プロセスで Flask サーバを実行できるようにするために、ファイルをいくつか編集します。

### /client/src/background.js

electron-builder のインストールで追加された/client/src/background.js の一番最後に下記内容を追記します。
このファイルは Vue アプリ実行前の画面作成と、その破棄を管理しています。
この設定で起動時に子プロセスを作成して app を実行し、またクライアント終了時に子プロセスとそこからフォークされたプロセスをまとめて終了するようになります。

```js
//...色々なデフォルトの設定
let pyProc = null;
const path = require("path");

const createPyProc = () => {
  let script = path.join(__dirname, "app");
  console.log("createing on ", script);
  pyProc = require("child_process").spawn(script, { detached: true });
  if (pyProc != null) {
    console.log("child process success");
  }
};

const exitPyProc = () => {
  // pyProc.kill()
  process.kill(-pyProc.pid);
  console.log("child process killed");
  pyProc = null;
};

app.on("ready", createPyProc);
app.on("will-quit", exitPyProc);
```

参考

Electron で子プロセスがフォークしたプロセスのキル https://azimi.me/2014/12/31/kill-child_process-node-js.html

### /client/src/App.vue

electron のモジュールを利用する場合には、必要に応じて作成済みのコンポーネントにも手を入れます。
今回は App.vue にファイルを開くダイアログを呼ぶモジュールを追加しています。
（すでに追加済みです）

## 実行
