# MetaGPT: マルチエージェントメタプログラミングフレームワーク

<p align="center">
<a href=""><img src="resources/MetaGPT-logo.jpeg" alt="MetaGPT ロゴ: GPT がソフトウェア会社で働けるようにし、協力してより複雑な仕事に取り組む。" width="150px"></a>
</p>

<p align="center">
<b>GPT にさまざまな役割を割り当てることで、複雑なタスクのための共同ソフトウェアエンティティを形成します。</b>
</p>

<p align="center">
<a href="README_CN.md"><img src="https://img.shields.io/badge/文档-中文版-blue.svg" alt="CN doc"></a>
<a href="../README.md"><img src="https://img.shields.io/badge/document-English-blue.svg" alt="EN doc"></a>
<a href="README_JA.md"><img src="https://img.shields.io/badge/ドキュメント-日本語-blue.svg" alt="JA doc"></a>
<a href="https://discord.gg/wCp6Q3fsAk"><img src="https://dcbadge.vercel.app/api/server/wCp6Q3fsAk?compact=true&style=flat" alt="Discord Follow"></a>
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
<a href="docs/ROADMAP.md"><img src="https://img.shields.io/badge/ROADMAP-路线图-blue" alt="roadmap"></a>
<a href="resources/MetaGPT-WeChat-Personal.jpeg"><img src="https://img.shields.io/badge/WeChat-微信-blue" alt="roadmap"></a>
<a href="https://twitter.com/DeepWisdom2019"><img src="https://img.shields.io/twitter/follow/MetaGPT?style=social" alt="Twitter Follow"></a>
</p>

1. MetaGPT は、**1 行の要件** を入力とし、**ユーザーストーリー / 競合分析 / 要件 / データ構造 / API / 文書など** を出力します。
2. MetaGPT には、**プロダクト マネージャー、アーキテクト、プロジェクト マネージャー、エンジニア** が含まれています。MetaGPT は、**ソフトウェア会社のプロセス全体を、慎重に調整された SOP とともに提供します。**
   1. `Code = SOP(Team)` が基本理念です。私たちは SOP を具体化し、LLM で構成されるチームに適用します。

![ソフトウェア会社は LLM ベースの役割で構成されている](resources/software_company_cd.jpeg)

<p align="center">ソフトウェア会社のマルチロール図式（順次導入）</p>

## 例（GPT-4 で完全生成）

例えば、`python startup.py "Toutiao のような RecSys をデザインする"`と入力すると、多くの出力が得られます

![Jinri Toutiao Recsys データと API デザイン](resources/workspace/content_rec_sys/resources/data_api_design.png)

解析と設計を含む 1 つの例を生成するのに、**$0.2** （GPT-4 の api のコスト）程度、完全なプロジェクトには **$2.0** 程度が必要です。

## インストール
### 伝統的なインストール
```bash
# ステップ 1: NPM がシステムにインストールされていることを確認してください。次に mermaid-js をインストールします。
npm --version
sudo npm install -g @mermaid-js/mermaid-cli

# ステップ 2: Python 3.9+ がシステムにインストールされていることを確認してください。これを確認するには:
python --version

# ステップ 3: リポジトリをローカルマシンにクローンし、インストールする。
git clone https://github.com/geekan/metagpt
cd metagpt
python setup.py install
```

### Docker によるインストール
```bash
# ステップ 1: metagpt 公式イメージをダウンロードし、config.yaml を準備する
docker pull metagpt/metagpt:v0.1
mkdir -p /opt/metagpt/config && docker run --rm metagpt/metagpt:v0.1 cat /app/metagpt/config/config.yaml > /opt/metagpt/config/config.yaml
vim /opt/metagpt/config/config.yaml # 設定を変更する

# ステップ 2: metagpt イメージを実行
docker run --name metagpt -d \
    -v /opt/metagpt/config:/app/metagpt/config \
    -v /opt/metagpt/workspace:/app/metagpt/workspace \
    metagpt/metagpt:v0.1

# ステップ 3: metagpt コンテナにアクセスする
docker exec -it metagpt /bin/bash

# ステップ 4: コンテナ内で遊ぶ
cd /app/metagpt
python startup.py "Write a cli snake game"
```

コマンド `docker run ...` は以下のことを行います:
- デフォルトのコマンド `tail -f /dev/null` で metagpt コンテナを起動する
- ホストディレクトリ `/opt/metagtp/config` をコンテナディレクトリ `/app/metagpt/config` にマップする
- ホストディレクトリ `/opt/metagpt/workspace` をコンテナディレクトリ `/app/metagpt/workspace` にマップする

### 自分でイメージをビルドする
```bash
# また、自分で metagpt イメージを構築することもできます。
cd metagpt && docker build --network host -t metagpt:v0.1 .
```

## 設定

- `OPENAI_API_KEY` を `config/key.yaml / config/config.yaml / env` のいずれかで設定します。
- 優先順位は: `config/key.yaml > config/config.yaml > env` の順です。

```bash
# 設定ファイルをコピーし、必要な修正を加える。
cp config/config.yaml config/key.yaml
```

| 変数名                                      | config/key.yaml                           | env                            |
|--------------------------------------------|-------------------------------------------|--------------------------------|
| OPENAI_API_KEY # 自分のキーに置き換える        | OPENAI_API_KEY: "sk-..."                  | export OPENAI_API_KEY="sk-..." |
| OPENAI_API_BASE # オプション                 | OPENAI_API_BASE: "https://<YOUR_SITE>/v1" | export OPENAI_API_BASE="https://<YOUR_SITE>/v1"   |

## チュートリアル: スタートアップの開始

```shell
python startup.py "Write a cli snake game"
```

スクリプトを実行すると、`workspace/` ディレクトリに新しいプロジェクトが見つかります。

### コードウォークスルー

```python
from metagpt.software_company import SoftwareCompany
from metagpt.roles import ProjectManager, ProductManager, Architect, Engineer

async def startup(idea: str, investment: float = 3.0, n_round: int = 5):
    """スタートアップを実行する。ボスになる。"""
    company = SoftwareCompany()
    company.hire([ProductManager(), Architect(), ProjectManager(), Engineer()])
    company.invest(investment)
    company.start_project(idea)
    await company.run(n_round=n_round)
```

`examples` でシングル・ロール（ナレッジ・ベース付き）と LLM のみの例を詳しく見ることができます。

## お問い合わせ先

このプロジェクトに関するご質問やご意見がございましたら、お気軽にお問い合わせください。皆様のご意見をお待ちしております！

- **Email:** alexanderwu@fuzhi.ai
- **GitHub Issues:** 技術的なお問い合わせについては、[GitHub リポジトリ](https://github.com/geekan/metagpt/issues) に新しい issue を作成することもできます。

ご質問には 2-3 営業日以内に回答いたします。

## デモ

https://github.com/geekan/MetaGPT/assets/2707039/5e8c1062-8c35-440f-bb20-2b0320f8d27d
