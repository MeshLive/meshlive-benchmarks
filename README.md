# MeshLive benchmark baseline

**Measured results of MeshLive on real phones, with inputs anyone can regenerate: a baseline to compare your own phones against.**

<p align="center">
  <a href="LICENSE"><img alt="Data licence: CC BY 4.0" src="https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey?style=for-the-badge"></a>
  <img alt="1,519 executions" src="https://img.shields.io/badge/executions-1%2C519-blue?style=for-the-badge">
  <img alt="362 distinct requests" src="https://img.shields.io/badge/requests-362-blue?style=for-the-badge">
  <img alt="Status: no full pass yet" src="https://img.shields.io/badge/status-no%20full%20pass%20yet-orange?style=for-the-badge">
</p>

<p align="center">
  <a href="https://github.com/MeshLive/meshlive-android">MeshLive for Android</a> ·
  <a href="https://github.com/MeshLive/meshlive-ios">MeshLive for iPhone</a> ·
  <a href="https://github.com/MeshLive">MeshLive organisation</a> ·
  <a href="https://github.com/MeshLive/meshlive-benchmarks/issues/new/choose">Ask about a result</a>
</p>

Measured results of MeshLive (Android, Bluetooth-only live video, calls and relayed streams) on real phones, published
so that anyone can regenerate the same inputs, run the same requests and compare their results with ours, request by
request. The app itself is at [MeshLive/meshlive-android](https://github.com/MeshLive/meshlive-android). The iPhone app
([MeshLive/meshlive-ios](https://github.com/MeshLive/meshlive-ios)) has no results here yet.

> **Read this first: no execution here is a full pass, by design.** An execution passes only when every family
> passes, and four families (camera, acoustic, physical latency, endurance) need measuring equipment that is not set
> up yet, so they are always `UNMEASURED`. Many executions also record real failures (connection, picture,
> smoothness) on development builds, many of which were fixed later. Compare the **per-family results and the
> stream metrics** for the same phone model and request, not the overall verdict.
>
> These are results from development builds leading up to 0.1.0-beta, on four reference phones, in one home radio
> environment. No camera frames, audio recordings, screenshots, Bluetooth traces, phone serials or addresses are
> included: only numbers, settings and the fingerprints and recipes of the generated inputs.

## Where to start

- **Just want the numbers?** Download [`index.html`](index.html) and open it in a browser (GitHub shows HTML files as
  source, not as a page). It is a self-contained summary table linking to every result. For a spreadsheet, use
  [`summary/baseline.csv`](summary/baseline.csv) (latest result per request) or [`summary/history.csv`](summary/history.csv)
  (every execution).
- **Want to compare your phones?** Follow [Reproduce and compare](#reproduce-and-compare). It needs the app repository,
  Python 3.13, adb and your own phones.
- **Want to know how to read a row?** Read [Status, honestly](#status-honestly) and [Caveats](#caveats) first.
- **Found something odd, or want to share results?** Use the [issue forms](https://github.com/MeshLive/meshlive-benchmarks/issues/new/choose).
  Please do not attach captures, logs with addresses or serial numbers, or anything else listed under [Privacy](#privacy).

## What is in it

| Path | Contents |
| --- | --- |
| `results/<suite>/<seq>-<case>.json` | One file per execution: the request, phones, build, inputs, gate results per family, stream metrics, and every analysis of that execution |
| `results/attempts-without-execution.json` | Selected cases that never produced an execution (blocked by preflight or a dependency, or interrupted while running). These are not results |
| `summary/baseline.csv` | Latest result per distinct request (`baseline_key`), with its build, failed families and history counts |
| `summary/history.csv` | Every execution in date order |
| `summary/builds.csv` | Tested builds: build ID, APK SHA-256, versionName, execution dates |
| `summary/counts.json` | Totals, status counts and exclusion counts |
| `inputs/manifest.json` | Every input used: ID, SHA-256 of every file, generator recipe, seed, mode, how to regenerate it, licence |
| `inputs/recipes/*.json` | The generator recipes (copied unchanged from `tools/video-stress-generator/examples`) |
| `tools/compare_baseline.py` | Joins your `suite-result.json` with this baseline by `baseline_key` |
| `tools/export_suite.py` | Exports selected baseline requests as a suite you can bind and run |

Coverage: 1,519 executions of 362 distinct requests between 2026-10-05 and 2026-10-10 (UTC) on 84 pre-release
builds, with four phones taking part: S24 (Samsung SM-S921B, Android 16), M31 (Samsung SM-M315F, Android 12), ASUS
(ASUS_I01WD, Android 11) and A15s (OPPO CPH2179, Android 10). There are 814 one-to-many stream executions, 26 chain
(relay) executions and 679 private calls. Transports: `ble` = LE L2CAP CoC, `gatt` = LE GATT, `classic` = RFCOMM.
The reference scope also names S22, Xiaomi and A55, but none of the qualifying executions used them.

### Status, honestly

No request has passed the full acceptance gates yet. Of the 1,519 executions, 1,226 are FAIL, 81 UNMEASURED, 145
PENDING_ANALYSIS (executed, then never scored) and 67 ANALYZING (scoring was interrupted). Latest status per request:
284 FAIL, 14 UNMEASURED, 64 PENDING_ANALYSIS. These rows are kept on purpose: a baseline that hides failures is useless.

- **FAIL**: at least one gate missed its limit. The v3 gates (`device-run-v3`) are strict: for example VMAF of at least
  90, SSIM of at least 0.98 and PSNR of at least 35 dB against the generated reference, zero freezes and drops, rolling
  p95 frame interval of at most 1.25 periods, discovery within 1.5 s and first picture within 3 s. A FAIL often means
  "worked, but below one strict gate". Read `families` and `stream_metrics` before drawing conclusions.
- **UNMEASURED**: a required measurement had no data or no adapter. Camera, acoustic, physical (glass-to-glass)
  latency and endurance have no adapter in these runs, so those families are always UNMEASURED.
- Some FAILs are infrastructure problems, kept as recorded: `Phone cleanup is unconfirmed` (14) and an analysis error
  `'time'` (5). They appear in `result.reason`.
- A result belongs to the build it ran on. A request whose latest execution used an older build is marked
  `on_newest_dataset_build = no`; it is not a result for a newer build.

## What qualifies (and what does not)

Only executions whose inputs anyone can regenerate byte-for-byte are included:

- video: raw I420 from `video-stress-generator` recipes (`coverage`, `quick-mosaic`, `framing`; `sustained` appears only
  in attempts), fed through the phone's real encoder;
- audio: the generator's own reference audio (cue tones and seeded noise) or `speech-v1` (openly licensed speech).
  Executions with no bound reference audio used the phone's live microphone. Those are included, marked `live-mic`,
  and their audio content is not reproducible. No audio was recorded or published here.

Excluded: 101 executions with live Camera2 input, 3 that used UVG / SVT natural clips (not redistributable), and the
142 older executions in the private historical ledger (17 camera, 37 UVG / SVT, 88 other non-regenerable inputs such
as recorded desk pans and removed clips). No generated encoded-replay runs exist in this period.

## Reproduce and compare

You need the MeshLive app repository (github.com/MeshLive/meshlive-android), Python 3.13, adb and your own phones.

1. **Generate inputs.** From the app repository root, for each input you need (see `inputs/manifest.json`):

   ```
   python -B tools/prepare_native_workload.py plan --recipe coverage --mode 640x480@15
   python -B tools/prepare_native_workload.py prepare --recipe coverage --mode 640x480@15 --output benchmarks/inputs/coverage-640x480-15 --max-bytes 2000000000
   ```

   Check the SHA-256 of `source.i420` and `reference_audio.wav` against the manifest. The tool refuses to run if the
   generator source (`19c0ef90...`) or the recipe hash differs. Pixel identity is promised only for the same
   generator version, seed and library versions (the manifest lists the environment: Python 3.13.3, NumPy 2.2.6,
   Pillow 11.3.0, OpenCV 4.12.0.88, SciPy 1.16.3, scikit-image 0.26.0). If a hash differs, your input is different:
   do not compare against this baseline until it matches. `speech-v1` WAVs are committed in the app repository
   (`benchmarks/inputs/speech-v1`); `tools/build_speech_reference.py verify` rebuilds and checks them.

2. **Export and bind the requests.** Map your phones to the baseline aliases in `tools/benchmark_devices.json` of the
   app repository, then:

   ```
   python -B PATH/meshlive-benchmarks/tools/export_suite.py --out-dir benchmarks/catalog/baseline-export --phones S24,M31
   python -B tools/bind_benchmark_inputs.py --suite benchmarks/catalog/baseline-export/baseline-bundle.json \
       --case baseline-<key> --fixtures benchmarks/inputs/coverage-640x480-15/raw-fixtures.json \
       --devices tools/benchmark_devices.json --output benchmarks/catalog/baseline-bound --with-reference-audio
   ```

   Use `--with-reference-audio` when the baseline audio is the generator's `reference_audio.wav`, the speech-attached
   fixtures manifest (`tools/build_speech_reference.py attach`) when it is `speech-v1`, and neither for `live-mic`. A
   call whose two phones send different modes needs one fixtures manifest that lists both modes. Binding gives new
   `raw-...` case IDs (they include local paths); the portable `baseline_key` stays the same. This export, bind and
   key round trip has been checked offline with regenerated inputs.

3. **Run** the bound bundle with `tools/run_benchmark_suite.py run` as described in `docs/TESTING.md` of the app
   repository, on a frozen APK, and finish analysis.

4. **Compare:**

   ```
   python -B PATH/meshlive-benchmarks/tools/compare_baseline.py --suite-result benchmarks/runs/YOUR_RUN/suite-result.json --csv compare.csv
   ```

   Use `--alias-map yourname=S24` if your registry uses other aliases. Results with no baseline entry are new requests.

`baseline_key` is the first 20 hex digits of the SHA-256 of the request in canonical JSON. The request is the scenario
with free-text fields, IDs, file paths and declared file metadata removed, phone aliases upper-cased, and inputs
replaced by their SHA-256 per phone (`case.request` in every result file). The key includes the phone aliases, so
"S24" means the role that phone played, not your hardware.

## Caveats

- **Phone- and firmware-specific.** Results depend on the exact model, firmware (`phones[].firmware_build`), Bluetooth
  controller and stack. Your S24 with other firmware is a different device.
- **Radio conditions were neither controlled nor measured.** Other Bluetooth and Wi-Fi traffic may have been present,
  and some phones had Wi-Fi on (suite names such as `wifioff` mark deliberate changes). Some suites ran pairs in parallel (`execution.concurrency = concurrent`); actual media
  overlap between lanes was not measured. Single executions are noisy: compare distributions over repeats, not one row.
- **Beta software.** All builds are pre-release debug builds made during active development. Many suites were
  short targeted checks or A/B experiments (`tunables` in the request names the experiment flags), not a balanced
  campaign.
- Decoder and TextureView timestamps are app-side proxies, not physical screen or speaker timing.
- Picture scores compare the decoded stream with the generated reference. They do not include on-screen rendering.

## Builds and the public repository

`build.build_id` is the first 8 hex digits of the tested APK's SHA-256 (full value in `build.apk_sha256`). All
builds are private development builds made before the public 0.1.0-beta release. Their `versionName` is `1.0` (read
from each retained APK; package `com.example.bluetoothtest`, renamed `io.github.meshlive.app` at release). The public
repository starts from a single scrubbed initial commit, so **private build IDs are opaque identifiers with no
matching public commit**. New contributions should record the public commit hash and `versionName` of the APK they
test (for example `0.1.0-beta`), plus its SHA-256.

## Privacy

This dataset contains no camera frames, images, video, audio recordings, screenshots, Bluetooth snoop logs or bug
reports. ADB serials, Bluetooth addresses, node IDs and key prefixes, local paths and personal names are removed or
replaced by phone aliases. Every file is checked by a blocking scanner before commit. App logs are not included.
Compressed, they would be about 620 MB (raw about 7.5 GB, mostly Bluetooth stack logs that also contain unrelated
nearby traffic), so they would need a separate scrubbing pass first.

## Sharing your results and citing this data

Results from other phones are welcome, including ones that fail. Open a "Share comparison results" issue with the
phone model and OS version, the app commit and APK SHA-256, the `baseline_key` values and the family-level outcome
(`tools/compare_baseline.py --csv` gives you these). Share summaries, not raw captures. Reports are not merged into the
baseline automatically; the maintainers re-run or review before anything is added.

To cite the data, name the repository and a commit, for example "MeshLive benchmark baseline,
github.com/MeshLive/meshlive-benchmarks, commit <short hash>, CC BY 4.0". Say which executions or `baseline_key`
values you used, because a request's latest result can change when the baseline is refreshed.

## Licence

Data in this repository (`results/`, `summary/`, `inputs/manifest.json`, `index.html`) under
**Creative Commons Attribution 4.0 International (CC BY 4.0)** (full text in [LICENSE](LICENSE)). The scripts in `tools/` are GPL-3.0-or-later, like the app; the recipe files in
`inputs/recipes/` are part of `video-stress-generator` (MIT). The
`speech-v1` sources keep their own licences (LibriSpeech CC BY 4.0, LibriVox public domain, Open Goldberg Variations
CC0), listed in the app repository.
