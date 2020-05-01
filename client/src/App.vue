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
      console.log(process.env.MY_PYTHON_APP_PATH)
      console.log(__dirname)
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
