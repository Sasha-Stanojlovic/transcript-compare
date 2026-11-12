# Transcript Compare

A small, standalone Python tool that retrieves two YouTube transcripts with the [Supadata](https://supadata.ai) API and compares their opening sections. It shows the first 60 seconds of each transcript and the first segment that mentions a keyword, then saves a Markdown report.

It uses only the Python standard library, so there is nothing to install beyond Python itself.

> **Referral notice:** The Supadata sign-up link below is my personal referral link. If you create a Supadata account through it, I may receive credits. You can also sign up at [supadata.ai](https://supadata.ai) directly.
>
> **Get a Supadata account:** [https://supadata.ai/r/SY8MHGCQ](https://supadata.ai/r/SY8MHGCQ)

Originally written as the companion code for a tutorial from [Content Genie](https://contentgenies.ai/).

## Features

- Retrieves timestamped YouTube transcripts through the Supadata API (native mode only, so it never triggers paid AI transcription by surprise).
- Lists the segments that start in the first 60 seconds of each video.
- Finds the first segment that contains your keyword or phrase.
- Caches successful responses locally for 30 days, so repeated runs do not spend API credits.
- Includes a `--demo` mode that runs offline with synthetic data, so you can see the output without an API key.

## Requirements

- Python 3.10 or newer
- A Supadata API key for live runs (not needed for `--demo`). Get one from the [Supadata dashboard](https://supadata.ai).

## Quick start

1. Clone or download this repository:

   ```bash
   git clone https://github.com/Sasha-Stanojlovic/transcript-compare.git
   cd transcript-compare
   ```

2. Run the offline demo (no API key or network needed):

   ```bash
   python3 compare_transcripts.py --demo
   ```

   This prints a report and saves it as `comparison.md` in the current folder.

3. Run a live comparison:

   ```bash
   python3 compare_transcripts.py
   ```

   The script asks for:
   - the first YouTube URL
   - the second YouTube URL
   - a topic keyword or phrase
   - your Supadata API key, if `SUPADATA_API_KEY` is not set

## Providing your API key

You have two options:

- **Environment variable (recommended for repeated use):**

  ```bash
  export SUPADATA_API_KEY="your-key-here"
  python3 compare_transcripts.py
  ```

- **Hidden prompt:** leave the variable unset, and the script asks for the key without displaying it.

Never commit your API key to the repository. The key is not written to the report or to the cache.

## Choosing good inputs

- Use two public YouTube videos that have captions available.
- Pick videos on a similar topic and for a similar audience. Two explanations of the same concept make the comparison more useful than two unrelated videos.
- Use a specific phrase if a single broad word produces irrelevant matches.

## Understanding the output

For each video, the report shows:

- the source label and URL
- the transcript language returned by Supadata (useful for spotting a fallback from your requested language)
- the timestamp of the first matching segment
- the segments that start within the first 60 seconds

Keep these limits in mind:

- Timestamps mark where a caption segment **begins**, not the exact moment a word is spoken.
- Keyword matching is literal. It can miss synonyms or differently worded references.
- A segment that starts before the 60-second boundary may run past it. The full segment is included so the sentence stays readable.
- The report describes transcript structure only. It does not show which video performs better. That requires real audience analytics.

## Caching

Successful transcripts are saved in `.transcript_cache/` for 30 days. The cache key is built from the submitted URL and request options. Delete that folder at any time to force fresh requests.

Failed responses and invalid data are never saved as successful transcripts.

## Error handling

| Message | What to do |
| --- | --- |
| `Supadata returned HTTP 401` or a key error | Check that your API key is valid and set correctly. |
| `Supadata returned HTTP 429` | You have hit a rate limit. Wait before trying again. |
| `No timestamped transcript was returned.` | The video may have no captions. Try a different captioned video. |
| `The transcript job has not finished yet.` | The job is still running. Try again shortly. |
| `Please enter a public HTTPS YouTube URL.` | Use a full `https://` YouTube or `youtu.be` link. |

Check your Supadata dashboard for account or credit issues.

## Ideas for extending it

- Normalize YouTube URLs to video IDs so different URL forms share one cache entry.
- Replace the local cache with a shared store so several users can reuse results.
- Send the excerpts and their timestamps to an LLM for script suggestions, keeping claims about performance separate from transcript evidence.

## Contributing

Contributions are welcome. Please open an issue to discuss larger changes first. Keep the script dependency-free unless there is a strong reason to add one.

## License

Released under the [MIT License](LICENSE).

## Disclosure

The tutorial this project came from was submitted as part of Supadata's credits program. The referral link above is a personal link from the person who published this repository.
