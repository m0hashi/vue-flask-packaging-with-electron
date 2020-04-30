# Vue-Flask Packaging with Electron

Vue, python(Flask), Electronを利用して,ローカル環境でファイルを操作するGUIアプリを作成します。

アプリは下記のシンプルな機能を持ちます。

- クライアント側でローカルのcsvを指定して、サーバー側に絶対パスをPOSTで渡す
- サーバは受け取った絶対パスにあるcsvファイルを読み取り、クライアントにjsonとして返却
- クライアントは受け取ったjsonファイルをテーブル形式で表示

最終的にElectronで1つの実行ファイルを作成して、pythonやnodejsの事前インストールなしにツールが使える形にします。 


# 動作確認
前提
python >= 3.7
nodejs >= 12.0


## 環境構築
アプリを動作させるためのpythonとvue, electronの環境を用意します。

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
Electronでサーバとクライアントをパッケージングする前に、それぞれのアプリが独立に実行できることを確認します。
ローカルフィアルの絶対パスを扱う都合上、クライアント側はブラウザではなくElectron上で実行します。
(環境構築でelectron-builderを導入することで、packages.jsonのscriptsにelectron:serveが追加されています。)

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

# Electron化手順
上記の動作確認ができた後、Electronで実行ファイルを1つにまとめます。
Flaskサーバ側のアプリを1つの実行ファイルにまとめ、クライアント起動時にそのFlaskサーバを子プロセスとして立ち上げる方針でパッケージングを行います。

## 環境構築
Vueとpythonで作成したElectron化前のアプリをpre-electronブランチに作成してあります。
この手順でパッケージ化できることを確認するため、そちらのブランチに切り替えて再度バッケージをインストール後、electron-builderをインストールします。

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

## pyhon
まずFlaskで作成したAPIサーバをpyinstallerを利用して、実行形式にパッケージングします。
--onefileでapp.pyに関連するファイルを1つにまとめ、--hidden-importでapp.pyから見えないものの必要なファイルを追加します。
今回の設定では、--distpathDirで指定したディレクトリに実行形式のファイルがappという名前で作成されます。
```sh
cd server
source ./venv/bin/activate
pyinstaller app/app.py --onefile --hidden-import pkg_resources.py2_warn --distpathDir ../client/electron_build
cd ..
```

## Vue
Vueクライアントの側では、クライアント起動時に子プロセスでFlaskサーバを実行できるようにするために、ファイルをいくつか編集します。

### /client/src/background.js
electron-builderのインストールで追加された/client/src/background.jsの一番最後に下記内容を追記します。
このファイルはVueアプリ実行前の画面作成と、その破棄を管理しています。
この設定で起動時に子プロセスを作成してappを実行し、またクライアント終了時に子プロセスとそこからフォークされたプロセスをまとめて終了するようになります。

```js
//...色々なデフォルトの設定
let pyProc = null
const path = require('path')

const createPyProc = () => {
  let script = path.join(__dirname, 'app')
  console.log('createing on ', script)
  pyProc = require('child_process').spawn(script, {detached: true})
  if (pyProc != null) {
    console.log('child process success')
  }
}

const exitPyProc = () => {
  // pyProc.kill()
  process.kill(-pyProc.pid)
  console.log('child process killed')
  pyProc = null
}

app.on('ready', createPyProc)
app.on('will-quit', exitPyProc)
```

参考

Electronで子プロセスがフォークしたプロセスのキル https://azimi.me/2014/12/31/kill-child_process-node-js.html


### /client/src/App.vue
electronのモジュールを利用する場合には、必要に応じて作成済みのコンポーネントにも手を入れます。
今回はApp.vueにファイルを開くダイアログを呼ぶモジュールを追加しています。
（すでに追加済みです）


## 実行


