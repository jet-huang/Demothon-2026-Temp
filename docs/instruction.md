# Instruction: Generate Presentation Video from Deck and Transcript

** Do NOT use AVATAR **

This document instructs an AI agent on how to produce a single presentation video by combining the slide deck with the speaker transcript.

## Inputs

- Slide deck: docs/introduction.pptx
- Speaker transcript: docs/transcript.md

## Output

- File: docs/introduction.mp4
- Container: MP4 (H.264 video, AAC audio)
- Resolution: 1920 x 1080, 30 fps
- Aspect ratio: 16:9
- Audio: stereo, 48 kHz, voice-over track plus optional low-volume background

## Global Constraints

- Spoken language: en-US
- Total runtime: not greater than five minutes (300 seconds)
- Narrator voice: single neutral en-US voice, professional and calm, presenter cadence around 150 to 160 words per minute
- Do not modify docs/introduction.pptx
- Do not add filler narration that is not present in docs/transcript.md
- Do not synthesize speech for slides that are explicitly marked as silent transitions in the transcript

## Slide-to-Transcript Mapping

1. Use the section headers in docs/transcript.md (Slide 1 through Slide 6) as the authoritative map to slide order.
2. For each Slide N section, render slide N of the deck as the visual and synthesize the section body as the voice-over.
3. Advance to the next slide when the voice-over for the current section ends, plus a 300 ms hold.
4. Do not process any slide beyond Slide 6. Slides 7, 8, and 9 of docs/introduction.pptx exist in the source file but are out of scope for this video.

## Per-Slide Rules

- Slide 1: render the title slide. Narration should start within the first 500 ms.
- Slide 2: long narration section. Keep the static slide visible for the full duration. No automatic bullet build-in animations unless they already exist in the deck.
- Slide 3: architecture diagram. Optional subtle camera pan or zoom toward the agents region during the sentence that mentions the four specialist agents. Do not add new graphics.
- Slide 4: setup. Short narration. Hold the slide.
- Slide 5: live demo. This slide has two segments.
    1. Promotion Video segment: 30 seconds, beats are listed explicitly in docs/transcript.md (0-5s, 5-12s, 12-20s, 20-26s, 26-30s). Render this as an inline 30-second sub-video composited on top of the Live Demo slide. Each beat should match the on-screen action described in the transcript. Voice-over follows the script text for that beat.
    2. Live demo narration segment: continue with the remaining narration text in the Slide 5 section, over the same Live Demo slide. Target about 50 seconds.
- Slide 6: closing summary. Narrate the full section, then hold for 1.5 seconds before fading to black. This is the final slide of the video.

## Timing Budget

- Slide 1: about 15 seconds
- Slide 2: about 75 seconds
- Slide 3: about 50 seconds
- Slide 4: about 20 seconds
- Slide 5: about 80 seconds (30 seconds promo video plus about 50 seconds live demo narration)
- Slide 6: about 35 seconds
- Total: about 275 seconds

If synthesized narration overruns, prioritize trimming the live demo narration on Slide 5 first. Never cut the Promotion Video beats and never cut the Slide 2 content.

## Promotion Video Sub-Clip Specification

- Duration: exactly 30 seconds
- Visual style: phone-frame mockup of the agency app, matching the brand assets in docs/assets/ if present
- Voice-over: read the beat lines from the Slide 5 Promotion Video script in docs/transcript.md
- Closing line at 26 to 30 seconds must be both spoken and shown on screen: One disruption. One coherent plan. Powered by Solace.

## Transitions and Motion

- Slide transition: simple cross-fade, 200 ms
- No flashy wipes, no decorative motion graphics, no emoji overlays
- No text or watermark beyond what is already in the deck

## Audio

- Voice-over track: full level, peak around -3 dBFS
- Optional background music: instrumental, ambient, ducked to at least -18 dBFS under voice. Mute background during the Promotion Video sub-clip if it would clash with its own audio bed.
- No sound effects beyond what the Promotion Video sub-clip needs to feel like a phone app demo

## Acceptance Criteria

1. Total runtime is between 250 seconds and 300 seconds.
2. Every Slide N section in docs/transcript.md (Slide 1 through Slide 6) is represented in the video in order.
3. Spoken text matches the transcript verbatim, with only natural disfluency removal allowed.
4. The Live Demo slide contains a 30-second Promotion Video sub-clip with all five beats present and on time, followed by about 50 seconds of live demo narration.
5. The video ends on Slide 6. Slides 7 through 9 of the deck are not rendered or narrated.
6. Output is a single MP4 file at docs/introduction.mp4.

## Failure Handling

- If a slide cannot be rendered from the pptx, fall back to a solid background using the deck's primary brand color and overlay the slide title text. Do not block the whole render on one slide.
- If voice synthesis fails for a section, retry once, then fall back to a different neutral en-US voice from the same vendor. Do not drop the section.
- If total runtime exceeds 300 seconds after generation, re-render with a 5 percent faster narration rate rather than cutting transcript content.

## Related Files

- [Transcript](transcript.md)
- [Demo Plan](demo-plan.md)
- [Demo Runbook](demo-runbook.md)
