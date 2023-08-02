# MetaGPT: マルチエージェントフレームワーク

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

**注:**

- すでに Chrome、Chromium、MS Edge がインストールされている場合は、環境変数 `PUPPETEER_SKIP_CHROMIUM_DOWNLOAD` を `true` に設定することで、
Chromium のダウンロードをスキップすることができます。

- このツールをグローバルにインストールする[問題を抱えている](https://github.com/mermaidjs/mermaid.cli/issues/15)人もいます。ローカルにインストールするのが代替の解決策です、

    ```bash
    npm install @mermaid-js/mermaid-cli
    ```

- config.yml に mmdc のコンフィギュレーションを記述するのを忘れないこと

    ```yml
    PUPPETEER_CONFIG: "./config/puppeteer-config.json"
    MMDC: "./node_modules/.bin/mmdc"
    ```

### Docker によるインストール

```bash
# ステップ 1: metagpt 公式イメージをダウンロードし、config.yaml を準備する
docker pull metagpt/metagpt:v0.3
mkdir -p /opt/metagpt/{config,workspace}
docker run --rm metagpt/metagpt:v0.3 cat /app/metagpt/config/config.yaml > /opt/metagpt/config/config.yaml
vim /opt/metagpt/config/config.yaml # 設定を変更する

# ステップ 2: コンテナで metagpt デモを実行する
docker run --rm \
    --privileged \
    -v /opt/metagpt/config:/app/metagpt/config \
    -v /opt/metagpt/workspace:/app/metagpt/workspace \
    metagpt/metagpt:v0.3 \
    python startup.py "Write a cli snake game"

# コンテナを起動し、その中でコマンドを実行することもできます
docker run --name metagpt -d \
    --privileged \
    -v /opt/metagpt/config:/app/metagpt/config \
    -v /opt/metagpt/workspace:/app/metagpt/workspace \
    metagpt/metagpt:v0.3

docker exec -it metagpt /bin/bash
$ python startup.py "Write a cli snake game"
```

コマンド `docker run ...` は以下のことを行います:

- 特権モードで実行し、ブラウザの実行権限を得る
- ホストディレクトリ `/opt/metagpt/config` をコンテナディレクトリ `/app/metagpt/config` にマップする
- ホストディレクトリ `/opt/metagpt/workspace` をコンテナディレクトリ `/app/metagpt/workspace` にマップする
- デモコマンド `python startup.py "Write a cli snake game"` を実行する

### 自分でイメージをビルドする

```bash
# また、自分で metagpt イメージを構築することもできます。
git clone https://github.com/geekan/MetaGPT.git
cd MetaGPT && docker build -t metagpt:v0.3 .
```

## 設定

- `OPENAI_API_KEY` を `config/key.yaml / config/config.yaml / env` のいずれかで設定します。
- 優先順位は: `config/key.yaml > config/config.yaml > env` の順です。

```bash
# 設定ファイルをコピーし、必要な修正を加える。
cp config/config.yaml config/key.yaml
```

| 変数名                                      | config/key.yaml                           | env                                             |
| ------------------------------------------ | ----------------------------------------- | ----------------------------------------------- |
| OPENAI_API_KEY # 自分のキーに置き換える    | OPENAI_API_KEY: "sk-..."                  | export OPENAI_API_KEY="sk-..."                  |
| OPENAI_API_BASE # オプション                 | OPENAI_API_BASE: "https://<YOUR_SITE>/v1" | export OPENAI_API_BASE="https://<YOUR_SITE>/v1" |

## チュートリアル: スタートアップの開始

```shell
python startup.py "Write a cli snake game"
# コードレビューを利用すれば、コストはかかるが、より良いコード品質を選ぶことができます。
python startup.py "Write a cli snake game" --code_review True
```

スクリプトを実行すると、`workspace/` ディレクトリに新しいプロジェクトが見つかります。

### 使用方法

```
NAME
    startup.py - We are a software startup comprised of AI. By investing in us, you are empowering a future filled with limitless possibilities.

SYNOPSIS
    startup.py IDEA <flags>

DESCRIPTION
    We are a software startup comprised of AI. By investing in us, you are empowering a future filled with limitless possibilities.

POSITIONAL ARGUMENTS
    IDEA
        Type: str
        Your innovative idea, such as "Creating a snake game."

FLAGS
    --investment=INVESTMENT
        Type: float
        Default: 3.0
        As an investor, you have the opportunity to contribute a certain dollar amount to this AI company.
    --n_round=N_ROUND
        Type: int
        Default: 5

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

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
