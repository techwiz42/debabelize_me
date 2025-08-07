# LinkedIn Post - Debabelizer Launch

**Introducing Debabelizer: A unified Python library for speech-to-text and text-to-speech**

After working with multiple voice processing APIs, we built Debabelizer to solve a common problem: each provider has different interfaces, authentication methods, and data formats.

**🎉 We're excited to announce that Debabelizer is now open source and in beta!** We're actively seeking feedback from developers who work with voice processing APIs.

Debabelizer provides a unified API that works with:
• STT: Soniox, Deepgram, Google Cloud, Azure, OpenAI Whisper
• TTS: ElevenLabs, OpenAI, Google Cloud, Azure

Key features:
- Consistent interface across all providers
- Real-time streaming support for most STT providers
- Real-time language auto-detection for 60+ languages (via Soniox)
- Provider auto-selection based on cost, latency, or quality preferences
- Easy provider switching without code changes

```python
# Same code works with any provider
processor = VoiceProcessor(stt_provider="soniox")
result = await processor.transcribe_file("audio.wav")
```

You can try it at debabelize.me, which demonstrates real-time transcription and synthesis using the library. *Note: This is our test environment and may be under construction from time to time.*

The package is now available on PyPI: `pip install debabelizer`

We built this because managing multiple voice APIs was becoming repetitive. The unified interface has saved development time on several projects.

**Beta Testing & Feedback**: As we're in beta, we'd love to hear from actual users! What voice processing challenges are you facing? Which providers would you like to see added? Your feedback will help shape the future of this project.

GitHub: github.com/techwiz42/debabelizer

#python #speechprocessing #ai #opensource

---

## Email Compatibility Note

**Markdown rendering in emails:**
- **Gmail, Outlook (web)**: No native markdown support
- **Outlook (desktop), Apple Mail**: No native markdown support
- **Specialized email clients**: Some support markdown (rare)

**Recommendation:** Use the HTML version for email clients.