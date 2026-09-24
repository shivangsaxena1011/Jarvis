# SHIVANI — YouTube Integration

## Overview
The YouTube integration (`integrations/youtube/service.py`) provides intelligent multimedia search, ranking, playback, and session controls.

## Capabilities
- **Semantic Search & Disambiguation**: Searches YouTube and ranks results using exact matching, channel relevance, and popularity.
- **Playback Controls**: Direct interaction with the HTML5 video element via JavaScript injection:
  - Play / Pause
  - Toggle Fullscreen
  - Toggle Mute / Volume adjustments
  - Like video
- **Resilient Fallbacks**: Detects video element presence and guarantees verified playback even in restricted environments.

## Registered Tools
- `youtube.open`: Opens YouTube homepage.
- `youtube.search`: Searches for videos and returns ranked candidates.
- `youtube.play`: Navigates to a specific video URL or title.
- `youtube.pause`: Pauses active playback.
- `youtube.resume`: Resumes active playback.
- `youtube.like`: Clicks the Like button.
- `youtube.fullscreen`: Toggles fullscreen playback.
