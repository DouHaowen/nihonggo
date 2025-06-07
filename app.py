# =====================
# 日语学习助手主程序
# =====================
# 本文件为 Streamlit 应用主入口，支持音视频上传、Whisper转写、GPT智能分句、翻译、假名标注、单句分析等功能。
# 每个主要步骤、变量、函数均添加详细中文注释，便于理解和维护。

import os
import tempfile
import base64
import subprocess
import sys
from moviepy.editor import VideoFileClip
import re
import difflib

from dotenv import load_dotenv
import streamlit as st
import openai

# 加载 .env 文件中的环境变量（如 OPENAI_API_KEY）
load_dotenv()

# ========== Streamlit Session State 初始化 ==========
# 用于跨页面/多次交互时保存变量
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'segments' not in st.session_state:
    st.session_state.segments = None
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = "中文"
if 'tmp_path' not in st.session_state:
    st.session_state.tmp_path = None
if 'show_manual' not in st.session_state:
    st.session_state.show_manual = True

# ========== API Key 检查与输入 ==========
def check_api_key():
    """
    检查用户是否已输入 OpenAI API Key。
    若未输入，则在侧边栏提示输入，输入后写入 session 并刷新页面。
    返回是否已设置 API key 的状态。
    """
    current_lang = LANGUAGE_MAPPINGS[st.session_state.selected_language]
    if st.session_state.api_key is None:
        st.warning(current_lang["api_key_warning"])
        api_key = st.text_input(current_lang["api_key_input"], type="password")
        if api_key:
            st.session_state.api_key = api_key
            openai.api_key = api_key
            st.success(current_lang["api_key_success"])
            st.rerun()
        return False
    return True

# ========== 多语言界面文本映射 ==========
LANGUAGE_MAPPINGS = {
    "中文": {
        "title": "🌸 日语学习助手",
        "upload_text": "上传音/视频文件",
        "start_button": "▶ 开始生成",
        "transcribing": "正在调用 Whisper 进行转写…",
        "sentence_analysis": "句子分析",
        "current_sentence": "当前句子：",
        "translation_system": "你是日文→中文专业翻译，只输出一句流畅的中文译文。",
        "reading_module": "🎧 单句朗读模块",
        "analysis_module": "📝 单句分析模块",
        "full_text": "全文",
        "hover_tip": "💡 将鼠标悬停在句子上，点击即可进行分析",
        "loop_play": "循环播放",
        "cancel_loop": "取消循环",
        "click_to_analyze": "点击分析此句",
        "api_key_warning": "请先输入您的 OpenAI API Key",
        "api_key_input": "OpenAI API Key",
        "api_key_success": "API Key 已设置！",
        "manual": """
    ### 📖 使用手册

    #### 🎯 系统功能
    本系统支持上传含有日语的音频或视频文件，提供以下学习功能：

    #### 🎧 单句朗读模块
    - 支持上传 MP4、MOV、MP3、WAV 格式的音频/视频文件
    - 自动生成日语字幕和中文翻译
    - 点击字幕可跳转到对应视频时间点
    - 支持单句循环播放功能，方便跟读练习
    - 当前播放句子会自动高亮显示

    #### 📝 单句分析模块
    - 显示完整的日语原文和中文翻译对照
    - 点击任意句子可进行深度分析
    - 分析内容包括：重要词汇（假名、词性、中文意思）和语法点（语法结构、用法说明、例句）

    #### 💡 使用提示
    - 上传文件后点击"开始生成"按钮
    - 等待系统处理完成后即可开始学习
    - 可以随时切换界面语言（中文/英文/韩文）
    - 建议先使用单句朗读模块进行跟读练习，再使用单句分析模块深入学习
    """
    },
    "English": {
        "title": "🌸 Japanese Learning Assistant",
        "upload_text": "Upload Audio/Video File",
        "start_button": "▶ Start Generation",
        "transcribing": "Transcribing with Whisper...",
        "sentence_analysis": "Sentence Analysis",
        "current_sentence": "Current Sentence: ",
        "translation_system": "You are a professional Japanese to English translator. Output only a fluent English translation.",
        "reading_module": "🎧 Single Sentence Reading Module",
        "analysis_module": "📝 Single Sentence Analysis Module",
        "full_text": "Full Text",
        "hover_tip": "💡 Hover over a sentence and click to analyze",
        "loop_play": "Loop Play",
        "cancel_loop": "Cancel Loop",
        "click_to_analyze": "Click to analyze",
        "api_key_warning": "Please enter your OpenAI API Key first",
        "api_key_input": "OpenAI API Key",
        "api_key_success": "API Key has been set!",
        "manual": """
    ### 📖 User Manual

    #### 🎯 System Features
    This system supports uploading Japanese audio or video files and provides the following learning features:

    #### 🎧 Single Sentence Reading Module
    - Supports uploading MP4, MOV, MP3, WAV format audio/video files
    - Automatically generates Japanese subtitles and English translations
    - Click on subtitles to jump to corresponding video timestamps
    - Supports single sentence loop playback for practice
    - Currently playing sentence is automatically highlighted

    #### 📝 Single Sentence Analysis Module
    - Displays complete Japanese text and English translation
    - Click any sentence for in-depth analysis
    - Analysis includes: important vocabulary (pronunciation, part of speech, meaning) and grammar points (structure, usage, examples)

    #### 💡 Usage Tips
    - Click 'Start Generation' after uploading a file
    - Wait for system processing to complete before starting
    - Switch interface language anytime (Chinese/English/Korean)
    - Recommended: practice with reading module first, then use analysis module for deeper learning
    """
    },
    "한국어": {
        "title": "🌸 일본어 학습 도우미",
        "upload_text": "오디오/비디오 파일 업로드",
        "start_button": "▶ 생성 시작",
        "transcribing": "Whisper로 전사 중...",
        "sentence_analysis": "문장 분석",
        "current_sentence": "현재 문장: ",
        "translation_system": "당신은 일본어→한국어 전문 번역가입니다. 유창한 한국어 번역만 출력하세요.",
        "reading_module": "🎧 단문장 읽기 모듈",
        "analysis_module": "📝 단문장 분석 모듈",
        "full_text": "전체 텍스트",
        "hover_tip": "💡 문장에 마우스를 올리고 클릭하여 분석",
        "loop_play": "반복 재생",
        "cancel_loop": "반복 취소",
        "click_to_analyze": "분석하려면 클릭",
        "api_key_warning": "OpenAI API Key를 먼저 입력해주세요",
        "api_key_input": "OpenAI API Key",
        "api_key_success": "API Key가 설정되었습니다!",
        "manual": """
    ### 📖 사용 설명서

    #### 🎯 시스템 기능
    이 시스템은 일본어 오디오 또는 비디오 파일을 업로드하고 다음 학습 기능을 제공합니다:

    #### 🎧 단문장 읽기 모듈
    - MP4, MOV, MP3, WAV 형식의 오디오/비디오 파일 업로드 지원
    - 일본어 자막과 한국어 번역 자동 생성
    - 자막 클릭 시 해당 비디오 시간으로 이동
    - 연습을 위한 단문장 반복 재생 지원
    - 현재 재생 중인 문장 자동 강조 표시

    #### 📝 단문장 분석 모듈
    - 완전한 일본어 텍스트와 한국어 번역 표시
    - 문장 클릭 시 심층 분석
    - 분석 내용: 중요 어휘(발음, 품사, 의미) 및 문법 포인트(구조, 용법, 예문)

    #### 💡 사용 팁
    - 파일 업로드 후 '생성 시작' 클릭
    - 시스템 처리가 완료될 때까지 대기
    - 언어 전환 가능(중국어/영어/한국어)
    - 권장: 읽기 모듈로 먼저 연습한 후 분석 모듈로 심화 학습
    """
    }
}

# ========== 页面配置与自定义样式 ==========
st.set_page_config(page_title="🌸 日语学习助手", layout="wide")

# 添加自定义 CSS 样式（美化标题、模块标题等）
st.markdown("""
<style>
    /* 标题样式 */
    .japanese-title {
        font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Meiryo", sans-serif;
        color: #333;
        text-align: center;
        padding: 20px;
        margin-bottom: 30px;
    }
    
    /* 模块标题样式 */
    .module-title {
        font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Meiryo", sans-serif;
        color: #2c3e50;
        border-left: 4px solid #e74c3c;
        padding-left: 10px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# ========== 侧边栏语言选择与文件上传 ==========
with st.sidebar:
    selected_language = st.selectbox(
        "选择语言 / Select Language / 언어 선택",
        options=list(LANGUAGE_MAPPINGS.keys()),
        index=list(LANGUAGE_MAPPINGS.keys()).index(st.session_state.selected_language)
    )
    st.session_state.selected_language = selected_language
    current_lang = LANGUAGE_MAPPINGS[selected_language]
    
    # 检查 API key
    has_api_key = check_api_key()
    
    # 文件上传控件，支持多种音视频格式
    uploaded = st.file_uploader(current_lang["upload_text"], type=['mp4', 'mp3', 'wav', 'mov'], disabled=not has_api_key)
    if uploaded and has_api_key:
        # 保存上传的临时文件
        suffix = os.path.splitext(uploaded.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.read())
            st.session_state.tmp_path = tmp.name
        # 生成按钮，点击后开始转写
        if st.button(current_lang["start_button"]):
            with st.spinner(current_lang["transcribing"]):
                input_file = st.session_state.tmp_path
                # 若为视频，先提取音频
                if input_file.lower().endswith(('.mp4', '.mov')):
                    try:
                        video = VideoFileClip(input_file)
                        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
                            temp_audio_path = temp_audio.name
                        video.audio.write_audiofile(temp_audio_path, codec='libmp3lame', fps=44100, nbytes=4, bitrate='192k')
                        video.close()
                        input_file = temp_audio_path
                    except Exception as e:
                        st.error(f"处理文件时出错: {str(e)}")
                        st.stop()
                # Whisper 语音转写
                try:
                    resp = openai.Audio.transcribe(
                        file=open(input_file, "rb"),
                        model="whisper-1",
                        response_format="verbose_json"
                    )
                    st.session_state.segments = resp.get("segments", [])
                    st.session_state.show_manual = False
                    st.rerun()
                except Exception as e:
                    st.error(f"转写过程中出错: {str(e)}")
                finally:
                    if input_file != st.session_state.tmp_path:
                        try:
                            os.unlink(input_file)
                        except:
                            pass

# ========== 主页面内容渲染 ==========
# 显示手册
st.markdown(f"""
<h1 class="japanese-title">{current_lang['title']}</h1>
""", unsafe_allow_html=True)
if st.session_state.show_manual:
    st.markdown(current_lang['manual'])

# ========== 时间戳格式化工具 ==========
def fmt(ts: float) -> str:
    """将秒数格式化为 00:00:00.000 字符串"""
    h = int(ts // 3600)
    m = int((ts % 3600) // 60)
    s = int(ts % 60)
    ms = int((ts - int(ts)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

# ========== Whisper转写后主流程 ==========
if st.session_state.segments:
    # 单句朗读模块标题
    st.markdown(f'<h2 class="module-title">{current_lang["reading_module"]}</h2>', unsafe_allow_html=True)
    # 取 Whisper 原始分句文本
    raw_sentences = [seg["text"].strip() for seg in st.session_state.segments]
    # 构造大模型合并分句的提示词
    merge_prompt = (
        "是自动语音识别分割的日语句子列表，部分句子被错误拆分。"
        "请你根据语义和语法，将应该合并的句子合并，输出合并后的完整日语句子列表（每句一行）：\n"
        + "\n".join(f"{i+1}. {s}" for i, s in enumerate(raw_sentences))
    )
    try:
        # 调用大模型智能合并分句
        merge_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是日语母语者，擅长根据语义和语法判断句子边界。"},
                {"role": "user", "content": merge_prompt}
            ]
        )
        # 去除编号，只保留内容
        merged_sentences = [re.sub(r'^[0-9]+[.、]\s*', '', line.strip()) for line in merge_response.choices[0].message.content.splitlines() if line.strip()]
        # 用 Whisper 的第一句和大模型第一句做相似度判断，防止大模型输出提示语
        first_raw = raw_sentences[0]
        if merged_sentences:
            first_merged = merged_sentences[0]
            similarity = difflib.SequenceMatcher(None, first_raw, first_merged).ratio()
            if similarity < 0.2:
                merged_sentences = merged_sentences[1:]
    except Exception as e:
        st.error(f"智能合并分句时出错: {str(e)}，将使用原始分句。")
        merged_sentences = raw_sentences

    # 生成 WebVTT 字幕和全文分析数据
    vtt = "WEBVTT\n\n"
    transcript_data = []
    for i, ja in enumerate(merged_sentences, start=1):
        # 计算每句的起止时间戳
        start_ts = fmt(st.session_state.segments[0]["start"]) if i == 1 else fmt(st.session_state.segments[i-1]["end"])
        end_ts = fmt(st.session_state.segments[i]["end"]) if i < len(st.session_state.segments) else fmt(st.session_state.segments[-1]["end"])
        # 翻译日文到中文
        chat = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"{current_lang['translation_system']} 注意：这是一个日语学习系统，请确保翻译的准确性和流畅性。如果遇到不完整的句子片段，请根据上下文理解完整意思后再翻译。翻译时要注意保持日语的语言特点和表达方式。"},
                {"role": "user", "content": ja}
            ]
        )
        zh = chat.choices[0].message.content.strip()
        # 获取带假名的日文
        furigana_chat = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一个日语专家。请将以下日语句子转换为带假名的格式，使用HTML的ruby标签。只对汉字添加假名读音，假名部分保持原样。如果遇到不完整的句子片段，请根据上下文理解完整意思后再添加假名。确保假名标注的准确性和完整性。例如：<ruby>日本語<rt>にほんご</rt></ruby>を<ruby>勉強<rt>べんきょう</rt></ruby>する。只输出转换后的文本。"},
                {"role": "user", "content": ja}
            ]
        )
        ja_with_furigana = furigana_chat.choices[0].message.content.strip()
        # 存储每句的分析数据
        transcript_data.append({
            "index": i,
            "start": start_ts,
            "end": end_ts,
            "ja": ja,
            "zh": zh,
            "ja_with_furigana": ja_with_furigana
        })
        # 拼接 VTT 字幕内容
        vtt += f"{i}\n{start_ts} --> {end_ts}\n{ja}\n{zh}\n\n"

    # Base64 编码视频和 VTT
    with open(st.session_state.tmp_path, 'rb') as f:
        video_b64 = base64.b64encode(f.read()).decode()
    subtitle_b64 = base64.b64encode(vtt.encode()).decode()

    # 构建全文翻译 HTML
    transcript_html = ""
    for item in transcript_data:
        transcript_html += f"""
        <div class="transcript-line" id="line-{item['index']}" onclick="handleSentenceClick({item['index']}, '{item['start']}', '{item['ja']}')" data-start="{item['start']}" data-end="{item['end']}">
          <div class="ja">{item['ja_with_furigana']}</div>
          <div class="zh">{item['zh']}</div>
          <div class="button-group">
            <button class="loop-button" onclick="handleLoopPlay({item['index']}, '{item['start']}', '{item['end']}')">{current_lang['loop_play']}</button>
            <button class="cancel-loop-button" onclick="handleCancelLoop({item['index']})" style="display: none;">{current_lang['cancel_loop']}</button>
          </div>
        </div>
        """

    # 综合 HTML: 左侧视频，不显示自带字幕；右侧全文并红色高亮当前句式
    html = f"""
    <style>
      .container {{ display: flex; }}
      .video-section {{ flex: 2; padding-right: 16px; }}
      .transcript-section {{ flex: 1; max-height: 600px; overflow-y: auto; border-left: 1px solid #ddd; padding-left: 16px; }}
      .video-container {{ position: relative; width: 100%; padding-top: 56.25%; }}
      .video-container video {{ position: absolute; top:0; left:0; width:100%; height:100%; object-fit:contain; }}

      /* 隐藏 video 自带字幕渲染 */
      video::cue {{ display: none; }}

      .transcript-line {{ 
        padding: 8px; 
        transition: background 0.3s; 
        cursor: pointer;
        border-radius: 4px;
        position: relative;
        margin-bottom: 12px;
        border-bottom: 1px solid #eee;
      }}
      .transcript-line:hover {{ 
        background: #f0f0f0; 
      }}
      .transcript-line.highlight {{ 
        background: #ffcccc; 
      }}
      .ja {{ 
        margin-left: 8px; 
        color: #1a73e8; 
        font-size: 1.2em; 
        font-weight: 500;
        margin-bottom: 4px;
        line-height: 2;
      }}
      .ja ruby {{
        ruby-position: over;
        ruby-align: center;
      }}
      .ja rt {{
        font-size: 0.65em;
        color: #666;
        font-weight: normal;
        padding: 0 1px;
      }}
      .zh {{ 
        margin-left: 8px; 
        color: #333; 
        font-size: 1.1em;
        padding-left: 12px;
        border-left: 3px solid #1a73e8;
        line-height: 1.4;
      }}

      .button-group {{
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        display: flex;
        gap: 8px;
        opacity: 0;
        transition: opacity 0.3s ease;
      }}

      .transcript-line:hover .button-group {{
        opacity: 1;
      }}

      .loop-button, .cancel-loop-button {{
        background: #4CAF50;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9em;
        min-width: 80px;
      }}

      .cancel-loop-button {{
        background: #f44336;
        display: none;
      }}

      .loop-button:hover {{
        background: #45a049;
      }}

      .cancel-loop-button:hover {{
        background: #d32f2f;
      }}

      .transcript-line.looping .loop-button {{
        display: none;
      }}

      .transcript-line.looping .cancel-loop-button {{
        display: block !important;
      }}

      .transcript-line.looping .button-group {{
        opacity: 1 !important;
      }}
    </style>
    <div class="container">
      <div class="video-section">
        <div class="video-container">
          <video id="vid" controls crossorigin>
            <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
            <track kind="subtitles" srclang="ja" label="日/中" src="data:text/vtt;base64,{subtitle_b64}" default>
          </video>
        </div>
      </div>
      <div class="transcript-section" id="full-transcript">
        {transcript_html}
      </div>
    </div>
    <script>
      const video = document.getElementById('vid');
      const transcriptSection = document.getElementById('full-transcript');
      let currentHighlightedIndex = null;
      let isManualHighlight = false;
      let loopInterval = null;
      let currentLoopingIndex = null;

      function clearHighlights() {{
        const lines = transcriptSection.getElementsByClassName('transcript-line');
        for (let line of lines) {{ 
          line.classList.remove('highlight');
          line.classList.remove('looping');
        }}
      }}

      function parseTimestamp(timestamp) {{
        const [time, ms] = timestamp.split('.');
        const [hours, minutes, seconds] = time.split(':');
        return parseFloat(hours) * 3600 + parseFloat(minutes) * 60 + parseFloat(seconds) + parseFloat('0.' + ms);
      }}

      function highlightSentence(index) {{
        clearHighlights();
        const el = document.getElementById('line-' + index);
        if (el) {{
          el.classList.add('highlight');
          el.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
          currentHighlightedIndex = index;
        }}
      }}

      function handleSentenceClick(index, timestamp, sentence) {{
        // 发送消息到 Streamlit
        window.parent.postMessage({{
          type: 'sentence_click',
          data: {{
            index: index,
            timestamp: timestamp,
            sentence: sentence
          }}
        }}, '*');

        // 跳转到视频时间点
        const totalSeconds = parseTimestamp(timestamp);
        video.currentTime = totalSeconds;
        
        // 高亮显示当前句子
        highlightSentence(index);
        isManualHighlight = true;

        // 设置一个定时器，在视频开始播放后重置手动高亮状态
        setTimeout(() => {{
          isManualHighlight = false;
        }}, 1000);
      }}

      function handleLoopPlay(index, startTime, endTime) {{
        // 阻止事件冒泡，防止触发句子的点击事件
        event.stopPropagation();
        
        // 清除之前的循环
        if (loopInterval) {{
          clearInterval(loopInterval);
        }}
        
        // 设置视频的当前时间到句子开始时间
        const startSeconds = parseTimestamp(startTime);
        const endSeconds = parseTimestamp(endTime);
        video.currentTime = startSeconds;
        
        // 播放视频
        video.play();
        
        // 设置循环播放
        loopInterval = setInterval(() => {{
          if (video.currentTime >= endSeconds) {{
            video.currentTime = startSeconds;
          }}
        }}, 100);

        // 更新UI状态
        clearHighlights();
        const el = document.getElementById('line-' + index);
        if (el) {{
          el.classList.add('highlight');
          el.classList.add('looping');
          currentLoopingIndex = index;
        }}
      }}

      function handleCancelLoop(index) {{
        // 阻止事件冒泡
        event.stopPropagation();
        
        // 清除循环播放
        if (loopInterval) {{
          clearInterval(loopInterval);
          loopInterval = null;
        }}
        
        // 更新UI状态
        const el = document.getElementById('line-' + index);
        if (el) {{
          el.classList.remove('looping');
        }}
        currentLoopingIndex = null;
        
        // 继续播放视频
        video.play();
      }}

      video.addEventListener('loadedmetadata', () => {{
        const track = video.textTracks[0];
        track.mode = 'hidden';  // 隐藏渲染但保留 cue 事件

        track.addEventListener('cuechange', () => {{
          const activeCues = track.activeCues;
          if (activeCues.length > 0) {{
            const cue = activeCues[0];
            const cues = track.cues;
            for (let i = 0; i < cues.length; i++) {{
              if (cues[i] === cue) {{
                const idx = i + 1;
                // 只有在没有手动高亮且没有循环播放时才自动更新高亮
                if (!isManualHighlight && !currentLoopingIndex) {{
                  highlightSentence(idx);
                }}
                break;
              }}
            }}
          }}
        }});

        // 添加视频播放事件监听
        video.addEventListener('play', () => {{
          // 开始播放时重置手动高亮状态
          isManualHighlight = false;
        }});

        video.addEventListener('pause', () => {{
          // 暂停时清除循环播放
          if (loopInterval) {{
            clearInterval(loopInterval);
            loopInterval = null;
            if (currentLoopingIndex) {{
              const el = document.getElementById('line-' + currentLoopingIndex);
              if (el) {{
                el.classList.remove('looping');
              }}
              currentLoopingIndex = null;
            }}
          }}
        }});
      }});
    </script>
    """

    st.components.v1.html(html, height=650, scrolling=False)

    # 添加模块标题
    st.markdown(f'<h2 class="module-title">{current_lang["analysis_module"]}</h2>', unsafe_allow_html=True)
    st.markdown(f"#### {current_lang['full_text']}")
    
    # 初始化 session state 用于存储点击的句子和分析结果
    if 'clicked_sentence' not in st.session_state:
        st.session_state.clicked_sentence = None
    if 'last_analysis' not in st.session_state:
        st.session_state.last_analysis = None
    
    # 显示提示信息
    st.markdown(f"> <span style='color: #FFD700;'>{current_lang['hover_tip']}</span>", unsafe_allow_html=True)
    
    # 创建一个容器来显示全文
    full_text_container = st.container()
    
    # 在容器中显示全文
    with full_text_container:
        # 使用自定义CSS来优化布局
        st.markdown("""
        <style>
        .sentence-container {
            display: flex;
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 5px;
            background-color: #f8f9fa;
        }
        .sentence-container:hover {
            background-color: #f0f0f0;
        }
        .japanese-text {
            flex: 3;
            padding-right: 20px;
            border-right: 1px solid #dee2e6;
        }
        .chinese-text {
            flex: 1;
            padding-left: 20px;
            color: #666;
        }
        .sentence-number {
            color: #666;
            font-size: 0.9em;
            margin-right: 8px;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 为每个句子创建一个容器
        for item in transcript_data:
            # 创建两列布局
            cols = st.columns([3, 1])
            
            with cols[0]:
                # 日文原文按钮
                if st.button(
                    f"[{item['index']}] {item['ja']}",
                    key=f"sentence_{item['index']}",
                    help=current_lang['click_to_analyze'],
                    use_container_width=True
                ):
                    sentence = item["ja"]
                    st.session_state.clicked_sentence = sentence
                    
                    # 根据选择的语言设置分析提示
                    if selected_language == "中文":
                        analysis_prompt = f"""
                        请用中文详细分析以下日语句子，必须包含以下所有内容：

                        1. 重点词汇分析（请用表格形式展示）：
                        | 词汇 | 假名读音 | 词性 | 中文意思 | 使用场景 |
                        |------|----------|------|----------|----------|
                        | 词汇1 | 假名1 | 词性1 | 意思1 | 场景1 |
                        | 词汇2 | 假名2 | 词性2 | 意思2 | 场景2 |
                        ...

                        2. 语法点分析：
                           - 语法结构说明
                           - 用法解释
                           - 2-3个相关例句
                        
                        3. 句子整体分析：
                           - 句子类型（陈述句、疑问句等）
                           - 语气和语感
                           - 使用场景
                        
                        句子：{sentence}
                        """
                        system_prompt = "你是一个专业的日语教师，擅长用中文分析日语语法和词汇。请确保分析内容全面、准确、易懂。重点词汇分析必须使用表格形式展示。"
                    elif selected_language == "English":
                        analysis_prompt = f"""
                        Please analyze the following Japanese sentence in detail, including ALL of the following:

                        1. Important Vocabulary Analysis (Please present in table format):
                        | Vocabulary | Furigana | Part of Speech | English Meaning | Usage Context |
                        |------------|----------|----------------|-----------------|---------------|
                        | Word 1 | Furigana 1 | POS 1 | Meaning 1 | Context 1 |
                        | Word 2 | Furigana 2 | POS 2 | Meaning 2 | Context 2 |
                        ...

                        2. Grammar Point Analysis:
                           - Grammar structure explanation
                           - Usage explanation
                           - 2-3 related example sentences
                        
                        3. Overall Sentence Analysis:
                           - Sentence type (declarative, interrogative, etc.)
                           - Tone and nuance
                           - Usage context
                        
                        Sentence: {sentence}
                        """
                        system_prompt = "You are a professional Japanese teacher, skilled in analyzing Japanese grammar and vocabulary in English. Please ensure the analysis is comprehensive, accurate, and easy to understand. Important vocabulary analysis must be presented in table format."
                    else:  # 韩文
                        analysis_prompt = f"""
                        다음 일본어 문장을 상세히 분석해주세요. 다음 내용을 모두 포함해야 합니다:

                        1. 중요 어휘 분석 (표 형식으로 제시):
                        | 어휘 | 후리가나 | 품사 | 한국어 의미 | 사용 맥락 |
                        |------|----------|------|------------|----------|
                        | 어휘1 | 후리가나1 | 품사1 | 의미1 | 맥락1 |
                        | 어휘2 | 후리가나2 | 품사2 | 의미2 | 맥락2 |
                        ...

                        2. 문법 포인트 분석:
                           - 문법 구조 설명
                           - 용법 설명
                           - 관련 예문 2-3개
                        
                        3. 전체 문장 분석:
                           - 문장 유형 (평서문, 의문문 등)
                           - 어조와 뉘앙스
                           - 사용 맥락
                        
                        문장: {sentence}
                        """
                        system_prompt = "당신은 일본어 문법과 어휘를 한국어로 분석하는 전문 일본어 교사입니다. 분석이 포괄적이고 정확하며 이해하기 쉽도록 해주세요. 중요 어휘 분석은 반드시 표 형식으로 제시해야 합니다."
                    
                    try:
                        analysis = openai.ChatCompletion.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": analysis_prompt}
                            ]
                        )
                        
                        # 更新分析结果
                        st.session_state.last_analysis = analysis.choices[0].message.content
                        st.session_state.current_sentence = sentence
                    except Exception as e:
                        st.error(f"分析过程中出现错误: {str(e)}")
            
            with cols[1]:
                # 中文翻译
                st.markdown(
                    f"<div style='padding-top: 8px;'><span class='sentence-number'>[{item['index']}]</span>{item['zh']}</div>", 
                    unsafe_allow_html=True
                )
    
    # 显示分析结果
    if st.session_state.last_analysis:
        st.markdown("---")
        st.markdown(f"### {current_lang['sentence_analysis']}")
        st.markdown(f"**{current_lang['current_sentence']}** {st.session_state.current_sentence}")
        st.markdown(st.session_state.last_analysis)

st.snow()