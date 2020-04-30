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
source .venv/bin/activate
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

electronの子プロセスとしてサーバを起動できるように設定(サーバの手動での起動不要)
```sh
cd server
pyinstaller app/app.py --onefile --hidden-import pkg_resources.py2_warn 
export MY_PYTHON_APP_PATH=`readlink -f ./dist/app`
cd ../client
npm run electron:serve 
```

ビルドして実行
```sh
cd server
pyinstaller app/app.py --onefile --hidden-import pkg_resources.py2_warn 
export MY_PYTHON_APP_PATH=`readlink -f ./dist/app`
cd ../client
npm run electron:build
./dist_electron/client-0.1.0.AppImag
```

# Electron 化手順

Vue+pythonで作成したアプリを後からElectron化する手順を記載します。
ますFlask サーバ側のアプリを 1 つの実行ファイルにまとめ、クライアント起動時にその Flask サーバを子プロセスとして立ち上げる方針でパッケージングを行います。

## 環境構築

Vue と python で作成した Electron 化前のアプリを pre-electron ブランチに作成してあります。
この手順でパッケージ化できることを確認するため、そちらのブランチに切り替えて再度バッケージをインストール後、electron-builder をインストールします。


```sh
git checkout pre-electron
```

```sh
cd server
source .venv/bin/activate
pip install -r requirements.txt

cd ../client
npm install
vue add electron-builder #Electron化用のパッケージ
cd ..
```

注意
npm install electron-builderとすると、Electron本体が入らなかったり、packages.jsonのscripotsが更新されなかったりするので注意

## pyhon

まず Flask で作成した API サーバを pyinstaller を利用して、実行形式にビルドします。
--onefile で app.py に関連するファイルを 1 つにまとめ、--hidden-import で app.py から見えないものの必要なファイルを追加します。
ビルド後は出来上がったappの絶対パスをクライアント側が環境変数として参照できるよう、設定ファイルに書き込みます。

```sh
cd server
source .venv/bin/activate
pyinstaller app/app.py --onefile --hidden-import pkg_resources.py2_warn
export MY_APP_PATH=`readlink -f ./dist/app`
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
if(process.env.MY_PYTHON_APP_PATH)
{
try{
  let pyProc = null;
  let script = process.env.MY_PYTHON_APP_PATH
  
  const createPyProc = () => {
    console.log("createing at ", script);
    pyProc = require("child_process").spawn(script, { detached: true });
    if (pyProc != null) {
      console.log("child process spawned");
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
}catch(err){
  console.log("PYTHON_APP_PATHが設定されていまっせん。対象のアプリのパスを設定してください。")
}
}
```

参考

Electron で子プロセスがフォークしたプロセスのキル https://azimi.me/2014/12/31/kill-child_process-node-js.html

### /client/src/App.vue

electron のモジュールを利用する場合には、必要に応じて作成済みのコンポーネントにも手を入れます。
今回は App.vue にファイルを開くダイアログを呼ぶモジュールを追加しています。App.vueのコメントアウトされている箇所のコメントアウトを解除して下記状態にしてください。


```html
<template>
  <div id="app">
    <h1>Electron-Vue-Python testing</h1>
    <b-btn @click="openDialog">Select File</b-btn>

    <div v-if="!Boolean(filepath)">
      ファイルを選択してください。
    </div>

    <div v-else-if="Boolean(filepath)">
      下記ファイルが指定されました。<br />
      {{ filepath }}<br />
      Get Data押下で指定したデータをサーバ側で取得し、テーブルに表示します。<br />
      <b-btn @click="getpivot">Get Data</b-btn>
      <b-table sticky-header="calc(100vh - 120px)" :items="pivot.data">
      </b-table>
    </div>
  </div>
</template>

<script>
import axios from "axios";
const dialog = require("electron").remote.dialog;
export default {
  name: "app",
  data() {
    return {
      pivot: [],
      filepath: null,
    };
  },
  methods: {
    getpivot() {
      axios
        .post("http://localhost:5000/pivot", { filepath: this.filepath })
        .then((res) => {
          this.pivot = res.data;
        });
    },
    openDialog() {
      dialog
        .showOpenDialog(null, {
          properties: ["openFile"],
          title: "select a text file",
          defaultPath: ".",
        })
        .then((result) => {
          this.filepath = result.filePaths;
          console.log(result.filePaths);
        });
    },
  },
};
</script>

```

## 実行
開発モードで実行します。
ファイルの選択や選んだファイルの絶対パスの表示、データの取得等が正常に行われることを確認します。

```sh
cd client
npm run electron:serve
```

## ビルド
実行形式にビルドします。
dist_electronにファイルが出力されます。

```sh
cd cliend
npm run electron:build
```


## その他
### CORS( Cross-Origin Resource Sharing)
CORSの許可は server/app/app.py 内の下記コードで行っています。
CORS(app)とすることで、リクエストに対するレスポンスにAccess-Control-Allow-Headers属性を付与して、異なるオリジンのリソース対するリクエストを許可します。
developerツールのNetworksの欄でレスポンスヘッダにAccess-Control-Allow-Headersが付与されていることを確認できます。

```py
from flask import Flask
from flask_restful import Resource, Api
from resources import Pivot
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Allow CORS
api = Api(app)
api.add_resource(Pivot, '/pivot')
app.run(port=5000, debug=True)
```
