# Music engines

ACE-Step is the baseline, not the ceiling. Riff ships one adapter interface
behind three engines; the plugin names none of them outside `daw/adapters/`.

| Engine | Kind | Vocals | Max length | Stems | Needs |
|---|---|---|---|---|---|
| `acestep` | local HTTP (ACE-Step 1.5) | yes | 240 s | no | a running ACE-Step server, `DAW_ACESTEP_URL` (default `http://127.0.0.1:7860`) |
| `replicate` | hosted HTTPS (Meta MusicGen by default) | no | 120 s | no | `DAW_REPLICATE_TOKEN`; any model slug via `DAW_REPLICATE_MODEL` |
| `dryrun` | local ffmpeg tones | no | 600 s | yes (per-layer) | ffmpeg on `PATH` |

`dryrun` is not a music model. It exists so the manifest/version/stems/loudness
pipeline is testable and so a dead engine degrades into something audible it
clearly labels as a stand-in.

## Selection

Resolution order for every `daw_layer_generate` call:

1. the tool's `engine` argument (a name, or `auto`)
2. `project.json`'s `engine` (set with `daw_project_create(..., engine=...)`)
3. plugin config: `DAW_ENGINE`, else `config.json`'s `"engine"`, else `dryrun`

`auto` probes `acestep` → `replicate` → `dryrun` and takes the first engine whose
`available()` says yes. The pick is recorded on the track
(`engine`) alongside the request (`engine_requested: "auto"`) and the skipped
engines' reasons, so a manifest read months later still explains itself. When no
engine is available the tool returns the per-engine reasons, not "generation
failed".

## Configuration

`config.json` is read at call time from `DAW_CONFIG`, else
`~/.hermes/daw-config.json` (outside the plugin directory, so uninstalling the
plugin does not take the config with it):

```json
{
  "engine": "auto",
  "replicate_token": "r8_...",
  "replicate_model": "meta/musicgen"
}
```

Environment variables win over the file: `DAW_ENGINE`, `DAW_REPLICATE_TOKEN`,
`DAW_REPLICATE_MODEL`, `DAW_REPLICATE_API`, `DAW_REPLICATE_TIMEOUT`,
`DAW_REPLICATE_SEND_SEED`, `DAW_REPLICATE_INPUT_JSON`, `DAW_ACESTEP_URL`,
`DAW_ACESTEP_MODEL`.

`DAW_REPLICATE_INPUT_JSON` merges extra fields into the model input, because
hosted models disagree about their schema; the adapter sends only `prompt` and
`duration` by default rather than guessing.

## Adding an engine

One file in `daw/adapters/`, a factory in `registry.CATALOG`, and a name in the
alias table if it has an obvious misspelling. Implement:

```python
class Engine(Protocol):
    name: str
    def capabilities(self) -> Capabilities
    def available(self) -> tuple[bool, str]   # False + the exact fix
    def generate(self, request) -> Artifact   # ok=False carries error + hint
```

No engine may return `ok=True` without an artifact on disk, and none may raise a
traceback at the agent: `generate` raises `EngineUnavailable` only when called
directly while absent, and the core turns that into `{ok: false, hint}` first.
