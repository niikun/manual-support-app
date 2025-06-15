import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from dotenv import load_dotenv
import openai
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
import hashlib

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = 'audio'
VECTOR_DB_FOLDER = 'vector_db'
ALLOWED_EXTENSIONS = {'pdf'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)
if not os.path.exists(VECTOR_DB_FOLDER):
    os.makedirs(VECTOR_DB_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

openai.api_key = os.environ.get('OPENAI_API_KEY')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_hash(filename):
    """ファイルのハッシュ値を取得"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def create_vector_db(filename):
    """PDFからベクトルデータベースを作成"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_hash = get_file_hash(filename)
        db_path = os.path.join(VECTOR_DB_FOLDER, file_hash)
        
        # 既存のベクトルDBがあるかチェック
        if os.path.exists(db_path):
            embeddings = OpenAIEmbeddings()
            return Chroma(persist_directory=db_path, embedding_function=embeddings)
        
        # PDFからテキストを抽出
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            full_text = ""
            for i, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text:
                    full_text += f"[ページ {i+1}]\n{text}\n\n"
        
        # テキストをチャンクに分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        chunks = text_splitter.split_text(full_text)
        documents = [Document(page_content=chunk) for chunk in chunks]
        
        # ベクトル埋め込みとストア作成
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=db_path
        )
        
        return vectorstore
        
    except Exception as e:
        print(f"Error creating vector DB: {str(e)}")
        return None

def search_similar_chunks(filename, query, k=3):
    """類似チャンクを検索"""
    try:
        vectorstore = create_vector_db(filename)
        if vectorstore is None:
            return []
        
        similar_docs = vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in similar_docs]
        
    except Exception as e:
        print(f"Error searching similar chunks: {str(e)}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('ファイルが選択されていません')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('ファイルが選択されていません')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('ファイルがアップロードされました')
        return redirect(url_for('manual_detail', filename=filename))
    flash('PDFファイルを選択してください')
    return redirect(request.url)

@app.route('/manual/<filename>')
def manual_detail(filename):
    return render_template('manual_detail.html', filename=filename)

@app.route('/api/pages/<filename>')
def get_pages(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"Trying to read PDF file: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return jsonify({'error': 'ファイルが見つかりません'}), 404
        
        pages = []
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            print(f"PDF loaded successfully. Number of pages: {len(pdf_reader.pages)}")
            
            for i, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    pages.append({
                        'page': i + 1,
                        'text': text if text else 'テキストを抽出できませんでした'
                    })
                    print(f"Page {i+1} processed successfully")
                except Exception as page_error:
                    print(f"Error processing page {i+1}: {str(page_error)}")
                    pages.append({
                        'page': i + 1,
                        'text': f'ページ {i+1} の処理中にエラーが発生しました: {str(page_error)}'
                    })
        
        print(f"Total pages processed: {len(pages)}")
        return jsonify(pages)
    except Exception as e:
        print(f"Error in get_pages: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'PDFの読み込み中にエラーが発生しました: {str(e)}'}), 500

@app.route('/api/generate_audio/<filename>/<int:page>')
def generate_audio(filename, page):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            if page > len(pdf_reader.pages):
                return jsonify({'error': 'ページが存在しません'}), 404
            
            page_text = pdf_reader.pages[page - 1].extract_text()
            if not page_text or page_text.strip() == '':
                return jsonify({'error': 'このページからテキストを抽出できませんでした'}), 400
            
            client = openai.OpenAI()
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=page_text
            )
            
            audio_filename = f"{filename}_page_{page}.mp3"
            audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
            response.stream_to_file(audio_path)
            
            return jsonify({'audio_file': audio_filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_file(os.path.join(app.config['AUDIO_FOLDER'], filename))

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        manual_filename = data.get('manual_filename')
        question = data.get('question')
        
        if not manual_filename or not question:
            return jsonify({'error': 'ファイル名と質問が必要です'}), 400
        
        # RAGを使用して関連するチャンクを検索
        print(f"Searching for relevant chunks for question: {question}")
        relevant_chunks = search_similar_chunks(manual_filename, question, k=5)
        
        if not relevant_chunks:
            return jsonify({'error': 'マニュアルから関連する情報を見つけることができませんでした'}), 404
        
        # 関連チャンクを結合
        context = "\n\n".join(relevant_chunks)
        print(f"Found {len(relevant_chunks)} relevant chunks")
        
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"""あなたはマニュアルサポートアシスタントです。以下のマニュアルの関連部分に基づいて、ユーザーの質問に正確に答えてください。

マニュアルの関連部分:
{context}

回答の際は以下に注意してください：
1. マニュアルの内容に基づいて正確に回答する
2. 情報が不足している場合は、そのことを明記する
3. 安全に関わる内容は特に慎重に回答する
4. **必ず参照ページ情報を含める**：関連する内容が記載されているページ番号や章を明記する
5. 「詳細は○○ページをご参照ください」「△△章に詳しい説明があります」など具体的に案内する

回答の最後には必ず「詳細については、元のマニュアルの該当ページを確認してください。」を追加してください。"""},
                {"role": "user", "content": question}
            ],
            max_tokens=1000
        )
        
        return jsonify({'answer': response.choices[0].message.content})
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'質問応答中にエラーが発生しました: {str(e)}'}), 500

def generate_summary_from_chunks(filename):
    """RAGベースでマニュアル要約を生成"""
    try:
        # ベクトルDBを作成（または既存のものを取得）
        vectorstore = create_vector_db(filename)
        if vectorstore is None:
            return None
        
        # 要約に必要な重要なキーワードで検索
        important_queries = [
            "製品概要 機能 用途 仕様",
            "安全 注意事項 警告 禁止",
            "使用方法 操作手順 設定",
            "メンテナンス 保守 清掃 点検",
            "トラブルシューティング 問題 解決"
        ]
        
        all_chunks = []
        for query in important_queries:
            chunks = search_similar_chunks(filename, query, k=8)
            all_chunks.extend(chunks)
        
        # 重複を除去し、長さを制限
        unique_chunks = list(dict.fromkeys(all_chunks))
        
        # トークン制限を考慮してチャンクを制限
        context = ""
        for chunk in unique_chunks:
            if len(context) + len(chunk) < 12000:  # 安全なマージン
                context += chunk + "\n\n"
            else:
                break
        
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """あなたはマニュアル・取扱説明書の専門家です。以下のマニュアル内容を分析し、10000文字程度の非常に詳細で実用的な日本語要約を作成してください。

要約の構成（製品・サービス・ソフトウェアなど種類に関わらず適用）：
1. **概要**（目的、主要機能、用途、仕様、特徴）- 1500文字程度
2. **安全・注意事項**（重要な警告、禁止事項、リスク、前提条件）- 1500文字程度  
3. **詳細な使用・操作方法**（準備、セットアップ、基本操作、応用操作、設定方法、操作のコツ）- 5000文字程度
4. **保守・管理**（メンテナンス、清掃、点検、更新、保管方法）- 1500文字程度
5. **問題解決**（よくある問題、エラー対処、症状別解決方法）- 1000文字程度

特に使用・操作方法では以下を重視してください：
- 初心者でも理解できる段階的な手順
- 各機能の具体的な使い方
- 設定項目とその効果
- 効率的な操作方法とコツ
- よくある間違いとその回避方法

マニュアルの構成に沿って説明し、実際に使用する人が迷わず作業できるよう、具体的で分かりやすい表現を使用してください。
最後に「この要約は概要です。詳細な手順や重要な注意事項については、必ず元のマニュアルを参照してください。」という注意喚起を含めてください。"""},
                {"role": "user", "content": f"マニュアルの重要部分:\n{context}"}
            ],
            max_tokens=4000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error generating summary from chunks: {str(e)}")
        return None

@app.route('/api/generate_summary/<filename>')
def generate_summary(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'ファイルが見つかりません'}), 404
        
        # RAGベースで要約を生成
        summary_text = generate_summary_from_chunks(filename)
        
        if not summary_text:
            return jsonify({'error': '要約の生成に失敗しました'}), 500
        
        # 音声ファイル生成
        from openai import OpenAI
        client = OpenAI()
        audio_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=summary_text
        )
        
        audio_filename = f"{filename}_summary.mp3"
        audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
        audio_response.stream_to_file(audio_path)
        
        return jsonify({
            'summary': summary_text,
            'audio_file': audio_filename
        })
        
    except Exception as e:
        print(f"Error in generate_summary: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'要約生成中にエラーが発生しました: {str(e)}'}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
