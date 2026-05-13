import io
import logging
import os
import random
import wave
from datetime import datetime, timezone

from google import genai
from google.genai import types
from google.cloud import storage
from pydub import AudioSegment

from firestore_client import update_report_audio

logger = logging.getLogger(__name__)

VOICE_STYLE_PROMPT = """Narrate in a relaxed, conversational public-radio style with a dry, intelligent, lightly skeptical tone. Sound informed and prepared, but not formal or announcer-like. Keep the delivery warm, plainspoken, and human, with subtle wit and a faint raised-eyebrow quality when emphasizing uncertainty, contradiction, or weak logic.

Use a measured medium pace, clear diction, and natural phrasing. Avoid theatrical emotion, salesy enthusiasm, dramatic suspense, or overly polished "broadcast voice." The emotional delivery should feel curious, grounded, slightly wry, and confidently skeptical while remaining approachable and respectful."""

VOICES = [
    "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede",
    "Callirrhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba",
    "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar",
    "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird",
    "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat",
]
TTS_MODEL = "gemini-3.1-flash-tts-preview"


def build_podcast_script(report: dict) -> list[str]:
    title = report.get("title", "Untitled")
    tagline = report.get("tagline", "")

    sections = []

    intro = f"Welcome to Weekly Deep Dive. This week: {title}. {tagline}"
    sections.append(intro)

    if report.get("why_it_matters"):
        sections.append(f"Let's start with why this matters. {report['why_it_matters']}")

    if report.get("beginner"):
        sections.append(
            f"Starting at the beginner level. {report['beginner']}"
        )

    if report.get("intermediate"):
        sections.append(
            f"Moving to the intermediate level. {report['intermediate']}"
        )

    if report.get("advanced"):
        sections.append(
            f"Now for the advanced level. {report['advanced']}"
        )

    if report.get("key_takeaways"):
        sections.append(
            f"Here are the key takeaways. {report['key_takeaways']}"
        )

    sections.append(
        f"That's this week's deep dive into {title}. "
        "Thanks for listening, and we'll see you next week."
    )

    return sections


def _pcm_to_audio_segment(pcm_data: bytes) -> AudioSegment:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm_data)
    buf.seek(0)
    return AudioSegment.from_wav(buf)


def synthesize_audio(sections: list[str], report_id: str) -> dict:
    client = genai.Client(
        vertexai=True,
        project=os.environ.get("GCP_PROJECT", "dev-deep-dive"),
        location=os.environ.get("FUNCTION_REGION", "us-central1"),
    )

    voice_name = random.choice(VOICES)
    logger.info("Selected voice: %s", voice_name)

    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=1000)
    total_chars = 0

    for i, section in enumerate(sections):
        total_chars += len(section)
        logger.info("Synthesizing section %d/%d (%d chars)", i + 1, len(sections), len(section))

        response = client.models.generate_content(
            model=TTS_MODEL,
            contents=f"{VOICE_STYLE_PROMPT}\n\n{section}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name,
                        )
                    )
                ),
            ),
        )

        pcm_data = response.candidates[0].content.parts[0].inline_data.data
        segment = _pcm_to_audio_segment(pcm_data)

        if len(combined) > 0:
            combined += pause
        combined += segment

    logger.info("TTS synthesized %d chars, total duration %.1fs", total_chars, len(combined) / 1000)

    mp3_buf = io.BytesIO()
    combined.export(mp3_buf, format="mp3", bitrate="128k")
    mp3_bytes = mp3_buf.getvalue()

    bucket_name = os.environ.get("PODCAST_BUCKET", "dev-deep-dive-podcast")
    gcs_client = storage.Client()
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(f"episodes/{report_id}.mp3")
    blob.upload_from_string(mp3_bytes, content_type="audio/mpeg")

    audio_url = f"https://storage.googleapis.com/{bucket_name}/episodes/{report_id}.mp3"
    duration_secs = int(len(combined) / 1000)
    size_bytes = len(mp3_bytes)

    logger.info("Uploaded %d bytes to %s", size_bytes, audio_url)

    return {
        "audio_url": audio_url,
        "duration_secs": duration_secs,
        "size_bytes": size_bytes,
        "voice_name": voice_name,
        "model": TTS_MODEL,
    }


def generate_podcast_audio(report: dict, report_id: str) -> dict | None:
    if report.get("audio_url"):
        logger.warning("Audio already exists for report %s, skipping", report_id)
        return None

    sections = build_podcast_script(report)
    result = synthesize_audio(sections, report_id)

    update_report_audio(report_id, {
        "audio_url": result["audio_url"],
        "audio_duration_secs": result["duration_secs"],
        "audio_size_bytes": result["size_bytes"],
        "audio_voice_name": result["voice_name"],
        "audio_model": result["model"],
        "audio_generated_at": datetime.now(timezone.utc),
    })

    return result
