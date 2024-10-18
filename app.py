import os
import sys
import gradio as gr
import shutil
import re
from time import sleep

# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config_utils import load_key, update_key
from core.step1_ytdlp import download_video_ytdlp, find_video_files
from core.ask_gpt import ask_gpt

def on_tts_method_change(tts_method):
    if tts_method != load_key("tts_method"):
        update_key("tts_method", tts_method)
    return tts_method

def on_whisper_method_change(whisper_method):
    if whisper_method != load_key("whisper.method"):
        update_key("whisper.method", whisper_method)
    return whisper_method

def on_whisper_language_change(whisper_language):
    if whisper_language != load_key("whisper.language"):
        update_key("whisper.language", whisper_language)
    return whisper_language

def on_target_language_change(target_language):
    if target_language != load_key("target.language"):
        update_key("target.language", target_language)
    return target_language

def on_include_video_change(include_video):
    if include_video != (load_key("resolution") != "0x0"):
        update_key("resolution", "0x0" if not include_video else "1080p")
    return include_video

def on_resolution_change(resolution):
    if resolution != load_key("resolution"):
        update_key("resolution", resolution)
    return resolution

def on_original_volume_change(original_volume):
    if original_volume != load_key("original_volume"):
        update_key("original_volume", original_volume)
    return original_volume

def update_tts_settings(tts_method):
    if tts_method == "openai_tts":
        return {
            oai_voice: gr.Textbox(label="OpenAI Voice", value=load_key("openai_tts.voice"), visible=True),
            oai_tts_api_key: gr.Textbox(label="OpenAI TTS API Key", value=load_key("openai_tts.api_key"), visible=True),
            oai_api_base_url: gr.Textbox(label="OpenAI TTS API Base URL", value=load_key("openai_tts.base_url"), visible=True),
            fish_tts_base_url: gr.Textbox(visible=False),
            fish_tts_api_key: gr.Textbox(visible=False),
            azure_key: gr.Textbox(visible=False),
            azure_region: gr.Textbox(visible=False),
            azure_voice: gr.Textbox(visible=False),
            sovits_character: gr.Textbox(visible=False),
            selected_refer_mode: gr.Dropdown(visible=False)
        }
    elif tts_method == "fish_tts":
        return {
            oai_voice: gr.Textbox(visible=False),
            oai_tts_api_key: gr.Textbox(visible=False),
            oai_api_base_url: gr.Textbox(visible=False),
            fish_tts_base_url: gr.Textbox(label="Fish TTS Base URL", value=load_key("fish_tts.base_url"), visible=True),
            fish_tts_api_key: gr.Textbox(label="Fish TTS API Key", value=load_key("fish_tts.api_key"), visible=True),
            azure_key: gr.Textbox(visible=False),
            azure_region: gr.Textbox(visible=False),
            azure_voice: gr.Textbox(visible=False),
            sovits_character: gr.Textbox(visible=False),
            selected_refer_mode: gr.Dropdown(visible=False)
        }
    elif tts_method == "azure_tts":
        return {
            oai_voice: gr.Textbox(visible=False),
            oai_tts_api_key: gr.Textbox(visible=False),
            oai_api_base_url: gr.Textbox(visible=False),
            fish_tts_base_url: gr.Textbox(visible=False),
            fish_tts_api_key: gr.Textbox(visible=False),
            azure_key: gr.Textbox(label="Azure Key", value=load_key("azure_tts.key"), visible=True),
            azure_region: gr.Textbox(label="Azure Region", value=load_key("azure_tts.region"), visible=True),
            azure_voice: gr.Textbox(label="Azure Voice", value=load_key("azure_tts.voice"), visible=True),
            sovits_character: gr.Textbox(visible=False),
            selected_refer_mode: gr.Dropdown(visible=False)
        }
    elif tts_method == "gpt_sovits":
        return {
            oai_voice: gr.Textbox(visible=False),
            oai_tts_api_key: gr.Textbox(visible=False),
            oai_api_base_url: gr.Textbox(visible=False),
            fish_tts_base_url: gr.Textbox(visible=False),
            fish_tts_api_key: gr.Textbox(visible=False),
            azure_key: gr.Textbox(visible=False),
            azure_region: gr.Textbox(visible=False),
            azure_voice: gr.Textbox(visible=False),
            sovits_character: gr.Textbox(label="SoVITS Character", value=load_key("gpt_sovits.character"), visible=True),
            selected_refer_mode: gr.Dropdown(
                label="Refer Mode",
                choices=list(refer_mode_options.keys()),
                value=load_key("gpt_sovits.refer_mode"),
                type="index",
                info="配置 GPT-SoVITS 的参考音频模式",
                visible=True
            )
        }

def download_video(url, resolution):
    progress = gr.Progress("Downloading video...")
    download_video_ytdlp(url, resolution=resolution)
    progress.update(100)  # Assuming the download is complete
    video_file = find_video_files()
    return video_file

def delete_and_reselect():
    video_file = find_video_files()
    if video_file:
        os.remove(video_file)
        if os.path.exists("output"):
            shutil.rmtree("output")
        sleep(1)
    return None

def copy_local_video(local_path):
    if os.path.exists("output"):
        shutil.rmtree("output")
    os.makedirs("output", exist_ok=True)
    normalized_name = re.sub(r'[^\w\-_\.]', '', os.path.basename(local_path.name).replace(' ', '_'))
    shutil.copy(local_path.name, os.path.join("output", normalized_name))
    video_file = find_video_files()
    return video_file

def validate_api_key():
    response, _ = ask_gpt("This is a test, response 'message':'success' in json format.", response_json=True, log_title='None')
    if response and response.get('message') == 'success':
        return "API Key is valid"
    else:
        return "API Key is invalid"

with gr.Blocks(css=".column-form .wrap {flex-direction: column;} .centered-label {text-align: center;}") as app:
    with gr.Row():
        with gr.Column(visible=True, min_width=300, scale=1) as sidebar:
            gr.Markdown('<div style="text-align: center;"> # Settings</div>')
            with gr.Accordion("LLM Config", open=True):
                api_key = gr.Textbox(label="API_KEY", value=load_key("api.key"), elem_classes="centered-label")
                api_key.change(lambda x: update_key("api.key", x), inputs=[api_key], outputs=[])

                base_url = gr.Textbox(label="BASE_URL", value=load_key("api.base_url"), elem_classes="centered-label")
                base_url.change(lambda x: update_key("api.base_url", x), inputs=[base_url], outputs=[])

                model = gr.Textbox(label="MODEL", value=load_key("api.model"), elem_classes="centered-label")
                model.change(lambda x: update_key("api.model", x), inputs=[model], outputs=[])

                gr.Button("Validate API Key").click(
                    validate_api_key,
                    inputs=[],
                    outputs=gr.Textbox(label="Validation Status", elem_classes="centered-label")
                )

            with gr.Accordion("Subtitle Settings", open=True):
                whisper_method = gr.Dropdown(["whisperX 💻", "whisperX ☁️"], label="Whisper Method", value=load_key("whisper.method"), elem_classes="centered-label", allow_custom_value=True)
                whisper_method.change(on_whisper_method_change, inputs=[whisper_method], outputs=[whisper_method])

                whisper_language = gr.Dropdown(["en", "zh", "auto"], label="Whisper Language", value=load_key("whisper.language"), elem_classes="centered-label")
                whisper_language.change(on_whisper_language_change, inputs=[whisper_language], outputs=[whisper_language])

                target_language = gr.Textbox(label="Translation Target Language", value=load_key("target_language"), elem_classes="centered-label")
                target_language.change(on_target_language_change, inputs=[target_language], outputs=[target_language])

                include_video = gr.Checkbox(label="Include Video", value=load_key("resolution") != "0x0", elem_classes="centered-label")
                include_video.change(on_include_video_change, inputs=[include_video], outputs=[include_video])

                resolution = gr.Dropdown(["1080p", "360p"], label="Video Resolution", value=load_key("resolution"), elem_classes="centered-label", allow_custom_value=True)
                resolution.change(on_resolution_change, inputs=[resolution], outputs=[resolution])

            with gr.Accordion("Dubbing Settings", open=False):
                tts_method = gr.Dropdown(["openai_tts", "azure_tts", "gpt_sovits", "fish_tts"], label="TTS Method", value=load_key("tts_method"), elem_classes="centered-label")
                tts_method.change(on_tts_method_change, inputs=[tts_method], outputs=[tts_method])

                original_volume = gr.Dropdown(["Mute", "10%"], label="Original Volume", value=load_key("original_volume"), elem_classes="centered-label", allow_custom_value=True)
                original_volume.change(on_original_volume_change, inputs=[original_volume], outputs=[original_volume])

                oai_voice = gr.Textbox(label="OpenAI Voice", value=load_key("openai_tts.voice"), visible=False, elem_classes="centered-label")
                oai_voice.change(lambda x: update_key("openai_tts.voice", x), inputs=[oai_voice], outputs=[])

                oai_tts_api_key = gr.Textbox(label="OpenAI TTS API Key", value=load_key("openai_tts.api_key"), visible=False, elem_classes="centered-label")
                oai_tts_api_key.change(lambda x: update_key("openai_tts.api_key", x), inputs=[oai_tts_api_key], outputs=[])

                oai_api_base_url = gr.Textbox(label="OpenAI TTS API Base URL", value=load_key("openai_tts.base_url"), visible=False, elem_classes="centered-label")
                oai_api_base_url.change(lambda x: update_key("openai_tts.base_url", x), inputs=[oai_api_base_url], outputs=[])

                fish_tts_base_url = gr.Textbox(label="Fish TTS Base URL", value=load_key("fish_tts.base_url"), visible=False, elem_classes="centered-label")
                fish_tts_base_url.change(lambda x: update_key("fish_tts.base_url", x), inputs=[fish_tts_base_url], outputs=[])

                fish_tts_api_key = gr.Textbox(label="Fish TTS API Key", value=load_key("fish_tts.api_key"), visible=False, elem_classes="centered-label")
                fish_tts_api_key.change(lambda x: update_key("fish_tts.api_key", x), inputs=[fish_tts_api_key], outputs=[])

                azure_key = gr.Textbox(label="Azure Key", value=load_key("azure_tts.key"), visible=False, elem_classes="centered-label")
                azure_key.change(lambda x: update_key("azure_tts.key", x), inputs=[azure_key], outputs=[])

                azure_region = gr.Textbox(label="Azure Region", value=load_key("azure_tts.region"), visible=False, elem_classes="centered-label")
                azure_region.change(lambda x: update_key("azure_tts.region", x), inputs=[azure_region], outputs=[])

                azure_voice = gr.Textbox(label="Azure Voice", value=load_key("azure_tts.voice"), visible=False, elem_classes="centered-label")
                azure_voice.change(lambda x: update_key("azure_tts.voice", x), inputs=[azure_voice], outputs=[])

                sovits_character = gr.Textbox(label="SoVITS Character", value=load_key("gpt_sovits.character"), visible=False, elem_classes="centered-label")
                sovits_character.change(lambda x: update_key("gpt_sovits.character", x), inputs=[sovits_character], outputs=[])

                refer_mode_options = {1: "模式 1：仅用提供的参考音频", 2: "模式 2：仅用视频第 1 条语音做参考", 3: "模式 3：使用视频每一条语音做参考"}
                selected_refer_mode = gr.Dropdown(
                    label="Refer Mode",
                    choices=list(refer_mode_options.keys()),
                    value=load_key("gpt_sovits.refer_mode"),
                    type="index",
                    info="配置 GPT-SoVITS 的参考音频模式",
                    visible=False,
                    elem_classes="centered-label"
                )
                selected_refer_mode.change(lambda x: update_key("gpt_sovits.refer_mode", x), inputs=[selected_refer_mode], outputs=[])

                tts_method.change(update_tts_settings, inputs=[tts_method], outputs=[oai_voice, oai_tts_api_key, oai_api_base_url, fish_tts_base_url, fish_tts_api_key, azure_key, azure_region, azure_voice, sovits_character, selected_refer_mode])

        with gr.Column(scale=3) as main:
            gr.Markdown('<div style="text-align: center;">Main</div>')
            with gr.Accordion("Video Preparation", open=True):
                gr.Markdown('<div style="text-align: center;">Prepare Video</div>')
                video_preview = gr.Video()
                delete_button = gr.Button("Delete and Reselect", key="delete_video_button")
                delete_button.click(delete_and_reselect, inputs=[], outputs=video_preview)

                with gr.Column():
                        url = gr.Textbox(label="Enter YouTube Link")
                        resolution_dict = {
                            "360p": "360",
                            "1080p": "1080",
                            "Best": "best"
                        }
                        YTB_RESOLUTION = load_key("ytb_resolution")
                        resolution_options = list(resolution_dict.keys())
                        default_index = list(resolution_dict.values()).index(YTB_RESOLUTION) if YTB_RESOLUTION in resolution_dict.values() else 0
                        resolution_display = gr.Dropdown(label="Resolution", choices=resolution_options, value=resolution_options[default_index])
                        resolution = gr.State(resolution_dict[resolution_display.value])
                        download_button = gr.Button("Download Video", key="download_button", size="sm")

                        download_button.click(
                            download_video,
                            inputs=[url, resolution_display],
                            outputs=video_preview
                        )
                with gr.Column():
                    local_video_path = gr.File(label="Or Select Local Video File")
                    copy_local_video_button = gr.Button("Copy Local Video", key="copy_local_video_button", size="sm")
                    copy_local_video_button.click(
                        copy_local_video,
                        inputs=[local_video_path],
                        outputs=video_preview
                    )
            with gr.Accordion("Subtitles Processing", open=True):
                gr.Markdown('<div style="text-align: center;">Subtitles Processing</div>')
            with gr.Accordion("Video Processing", open=True):
                gr.Markdown('<div style="text-align: center;">Video Processing</div>')

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", debug=True)
