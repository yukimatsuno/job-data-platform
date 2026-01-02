import os
from openai import AzureOpenAI

# ===== Azure Foundry 設定 =====
client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version="2024-07-01-preview"
)

DEPLOYMENT_NAME = "arpitja-gpt-4o-mini"

# ===== system message（v2）=====
SYSTEM_MESSAGE = """
You are a data transformation and classification assistant.
You will receive a JSON object that contains a job posting scraped from a job website.
The input text may be written in Japanese or English.

Output rules:
- Output must be valid JSON only.
- Do not include explanations or markdown.
- Translate all content into natural English.
- If a field cannot be determined, use null.

Output format:
{
  "en_job_title": string,
  "en_description": string,
  "job_department": string,
  "job_role": string,
  "technologies": array of strings
}
"""

# ===== サンプル入力（あなたのJSON 1件）=====
JOB_JSON = {
    "url": "https://herp.careers/careers/companies/chowagiken/jobs/fwYoC2ChxlYY",
    "text": "株式会社調和技研\nの\nソフトウェアエンジニア\nの求人\n【フルリモート・フルフレックスOK】最先端AI研究開発を行う北大発認定ベンチャーにて受託・プロダクト開発を行うソフトウェアエンジニア募集！\n年収400～600万円\n正社員\nフルリモート\n求人概要\nJOB DESCRIPTION\nソフトウェアエンジニアとして、AIの受託開発を行っていただきます。\nまた、社内業務の標準化、効率化の推進や、社内利用サービスの管理、運用を担っていただきます。\n\n【受託開発】\nPoCフェーズ：\n・シンプルなGUIを持つ検証用システムの設計・実装\n・クライアントの課題に対応するAIモデルやデータ処理ロジックのデプロイ（AIモジュール部分はAIエンジニアが実装）\n本番フェーズ：\n・顧客環境（Azure, AWS, GCP, オンプレミスなど）に適したAIモジュールやAPIの実装\n・高品質なコードの開発、性能改善、およびリファクタリング\n・モジュールの顧客システムへの組み込み支援\n\n【開発環境・言語】\n・インフラ：AWS、GCP、Azure\n・構成管理：Terraform\n・言語：Python、JavaScript など\n・フレームワーク：FastAPI、React、Next.js、Tailwind CSS など\n・その他：Docker、GitHub\n\n\n＜業務内容の変更範囲＞\n雇入時：上記ご参照ください\n変更範囲：会社が定める業務\n\n求める人物像\nQUALIFICATIONS\n・独力でタスク遂行や技術選定できる方\n・コミュニケーションが得意な方\n・チームプレイが得意な方\n・新しいことにチャレンジできる方\n必須要件\nESSENTIAL CRIETERIA\n・Pythonを使用したアプリケーション開発経験（3年以上）\n・AI/MLまたはデータ処理に関する知識・経験\n・クラウド環境（AWS、GCP、Azureのいずれか）での開発経験\n・Webアプリケーションのバックエンドおよびフロントエンド開発経験\n歓迎要件\nDESIRABLE CRIETERIA\n・クラウド（AWS、GCP、Azure）に関する認定資格\n・LLMOps、MLOpsに関する知識\n・サーバ・ネットワーク・セキュリティに関する知識\n・アジャイル開発経験（スクラム、GitHubを使用したコード管理やレビューなど）\n・顧客折衝スキル\n・ネイティブレベルの日本語力\n・日本語非母語話者メンバーとのコミュニケーションができる英語力（目安：TOEIC700点以上）\n\n待遇・労働環境\nBENEFITS AND CONDITIONS\n給与\n年俸：400万円～600万円\n\n固定残業代あり\n・基本給：278,334円〜417,800円\n・固定残業代：55,000円〜82,200円（25時間分）\n・超過分は別途支給\n勤務地\nフルリモートワーク\nフルリモート勤務OK （国内であれば居住地は問いません）\n\n本社：北海道札幌市中央区南2条西12丁目324-2 902号室（屋内全面禁煙）\n東京支社：東京都中央区日本橋浜町2丁目1番10号ACN日本橋浜町ビル（屋内全面禁煙）\n\n\n＜就業場所の変更範囲＞\n雇入時：事業所所在地（札幌・東京）および当社が規定するテレワーク勤務の就業場所（労働者の自宅を含む）\n変更範囲：会社が定める場所\n雇用形態\n正社員\n勤務体系\n【就業時間】\nフルフレックスタイム制（コアタイム無）\n所定労働時間：8時間00分\n休憩：60分\n残業：有（平均残業時間：15時間）\n\n【休日休暇】\n年間休日数：125日\n完全週休二日制（土曜・日曜・祝日）\nその他（夏季休暇、年末年始休暇）\n有給休暇\n疾病休暇\n入社後特別有給休暇\n試用期間\n有 （3ヵ月）\n福利厚生\n健康保険・厚生年金・労災保険・雇用保険\n信託型有償ストックオプション制度あり\nフルリモートワーク可（国内居住地問わず）\nフレックスタイム制（コアタイム無し）\n在宅勤務手当支給\n通勤手当（実費精算）\n懇親会補助制度\n人事評価年2回\n時短勤務制度（応相談）\n出産・育児支援制度\nワーケーション制度\n資格取得支援\n書籍購入補助制度\nWindows/Mac選択可\n職務発明取扱規程あり\nリファラル採用支援制度\n副業可\n\n企業概要\nCOMPANY OVERVIEW\n本社所在地\n北海道札幌市中央区南2条西12丁目324-2 902\n設立\n2009-11\n資本金\n資本金 100,000,000円\nコーポレートサイト\nhttps://www.chowagiken.co.jp/\n\n求人の最終更新日時：2025/12/24 23:04"
}

response = client.chat.completions.create(
    model=DEPLOYMENT_NAME,
    messages=[
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": str(JOB_JSON)}
    ],
    temperature=0
)

print(response.choices[0].message.content)
