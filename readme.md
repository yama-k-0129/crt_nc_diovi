# ~2005年までの解析雨量 diovista形式変換

1. 環境構築（c言語）

- コマンドプロンプトに「wsl --install」を入力

https://learn.microsoft.com/ja-jp/windows/wsl/install


- Ubuntu 24.04.1 LTSをmicrosoft storeからダウンロード

- システム環境等の設定から「Linux用WIndowsサブシステム」にチェックを入れ、「OK」をクリックする。

https://qiita.com/fumigoro/items/a07f1e6f059ad4b2b3d2#visual-studio-code-の拡張機能の追加


- sudo apt updateがこのままだとうまくいかないので、大学ネットワーク以外のネットワークでダウンロードする



2. rapfile形式をtext形式に変換する

- ターミナルで「wsl」と入力
- 作業ディレクトリ（フォルダ）を作成し、そこに移動する「mkdir ~」「cd ~」
- 続いて、ターミナルで「code .」を入力するとvscodeを開く

左下の緑の部分に注目。WSL Ubuntu 20.04と表示されていると思いますが、「Windows側のVScodeがUbuntu側の実行環境を使って拡張機能などを動かす」という状態になっているという目印

これが表示されてればOK

フォルダーを全てVScodeで作成したフォルダーに移して、main.cの**24行目**にあるファイル名を変更して下さい


あとはVScodeの下のバーを引っ張ってVScode上でターミナルを開いたら、
「gcc MAIN.C RAPFILE.C -o rap2txt」
コマンドでRapfile.cとmain.cをコンパイルする


- 作成された実行ファイル　rap2txtを実行する「./rap2txt」


3. text形式をnetCDFに変換する

- txt2nc.pyを実行する（11行目のファイル名を変更する）

