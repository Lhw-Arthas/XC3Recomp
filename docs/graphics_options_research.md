# Research: PC-port-style graphics options for XCDE (2026-10-21, research only - nothing implemented)

User's question: can XCDE get the settings a modern PC game has (texture filtering, shadows, texture quality, draw
distance, HDR, Reflex, ...) without killing the PC? What does it render natively, what is upscaled?

Sources: the game's graphics config romfs/monolib/shader/lib_nx.ini (read at boot; we can already serve an edited
copy: romfs_virtual.c maybe_edit, T198), the keys the game's code knows (strings in main .ro, dumped to
<work dir>\nso\main_ro.txt, lines ~9900-10200), the render-target inventory of a field frame (LARECOMP_DEBUG_FRAME,
build/dbgcb3.log), our sampler code (textures.c ~1170), our scaling rule (textures.c tex_scalable).

## 1. What renders at what resolution today ("match" at 4K)
| Part | Size | Why |
|---|---|---|
| Scene (G-buffer 5 targets, depth, lighting, transparency, post, HUD) | full output (3x the Switch's 1280x720) | our scaling: every 16:9 target |
| Half-resolution effects (640x360 guest: transparencies `TransReduction` 0.5, AO / shadow mask `shadowHalf`, blur steps) | half of the output (1920x1080 at 4K) | the game's own choice, scaled with the output |
| Bloom / luminance chains (320x180 .. 20x12, 256x144, 128..4) | scaled / fixed | small, fine |
| **Shadow maps** (D32, 3 x 1024x1024 + 256x256) | **fixed 1024** | not 16:9 -> never scaled: soft / jagged shadow edges at 4K |
| Environment cubes / probes (64x64), sky / reflection (512x256) | fixed | not 16:9 |
| Character portraits (192x544) | scaled (T182) | |
| **Textures** | Switch assets as shipped | no higher-resolution data exists in the romfs |
| **Models / LOD** | Switch meshes, the game's LOD distances | |
Nothing is upscaled at "match" (the image is rendered at the window size; DLSS / FSR now optional).

## 2. What the game's own config exposes (lib_nx.ini; all keys the code reads are known)
Values today -> what a PC menu could offer:
- `AntiAliasing`, `tmaa` (+ tmaaSharpness_0..5, tmaaBlend*, tmaaNewUpScale): the game's temporal AA. **It uses
  camera jitter (`gJitter`) and a real velocity buffer (`gTVelocity`, `gToPrevScreen`)** - per-object motion vectors
  exist. Two consequences: (a) DLSS / FSR can be fed the game's own jitter + velocity instead of camera-only vectors
  (no ghosting on moving characters); (b) several effects are temporal and lean on TMAA: `tssao` (temporal SSAO,
  gTPrevSSAO), the raytraced / half-res shadow masks (gTPrevShwRaytrace, gTPrevShwHalf). Turning TMAA off (T198)
  leaves their per-frame noise visible = most likely the "noisy grass" the user saw. Better than "off": keep TMAA and
  sharpen it (tmaaSharpness*), or replace it by DLSS / FSR / DLAA fed with the game's jitter + velocity.
- `red_sclX/Y` = 1.0, `red_Auto = on`, `red_AtMinX/Y = 0.7`, `red_AtRate`: **the game's own dynamic resolution** (down
  to 70 % when it thinks the GPU is slow, then TMAA upscales). Must check whether it ever triggers on PC (it reads our
  emulated GPU timing); a "Dynamic resolution: off" option = `red_Auto=off`. Also a supersampling route
  (`red_scl` > 1?) to test.
- `TransReduction = on`, `trans_red_sclX/Y = 0.5`: transparencies (smoke, effects, water?) at half resolution ->
  "Effects quality: full resolution" (= 1.0).
- `shadowHalf = on`: shadow mask at half resolution -> "Shadow quality: high" (off). Plus our side: shadow maps 2x / 4x
  (1024 -> 2048 / 4096; the shaders get `gShwTexSize`, so filtering adapts) - the biggest visual gain for 4K.
- `ssao = off`, `tssao = on` (+ radius / intensity): ambient occlusion (classic SSAO is off, the temporal one on) ->
  "Ambient occlusion: off / TSSAO / TSSAO + SSAO".
- `ssr = on` (+ intensity / groundness): screen-space reflections -> on / off.
- `lensFlare = off` (lens_*): lens flares exist and are disabled -> option.
- `godray`, `lightShaft`, `bloom`, `shadowCloud` (cloud shadows), `blur2` (motion blur), `furBlur`, `dof`, `blur`:
  on / off toggles (motion blur / DOF already done).
- `tonemap`, `lut` / `luttex1` (colour grading LUT), `gamma`, `sRGBMode`, `tonemax/min/scale`: brightness / gamma /
  "colour grading on/off" sliders; the tonemap is where HDR would hook in.
- `cam_far = 80000`, `cam_near`: camera far plane (part of draw distance; LOD distances are elsewhere, in code / map
  data - research needed).
- `gpucount = 64`, `toonOutline*`, `rim_*`, `ibl*`, `wet*`: art parameters, leave alone.

## 3. What we can do in our renderer / runtime (independent of the game's config)
| Option | How | Cost | Effort |
|---|---|---|---|
| Anisotropic filtering 1x-16x | textures.c sampler: today we use the game's `max_aniso` (Switch values, often 1-4); force 16 for mipmapped textures (an env switch LARECOMP_SAMPLER_TEST already does it) | ~0 on a RTX, small on Vega 8 | low |
| Texture LOD bias / "texture sharpness" | sampler `mipLodBias` (negative = sharper, shimmer risk); with DLSS / FSR at lower internal res the standard bias is log2(render / output) | 0 | low |
| Shadow map resolution 2x / 4x | scale the 1024 / 256 depth targets (extend tex_scalable with a "shadow" class) | GPU: shadow passes x4 / x16 pixels (they're ~small) | medium |
| Sharpening (CAS / RCAS) | post pass in post_process (RCAS exists for FSR 1) | ~0.1 ms | low |
| HDR output (HDR10) | HDR swapchain (VK_COLOR_SPACE_HDR10_ST2084) + replace / follow the game's tonemap with an HDR tonemapper, HUD at a paper-white level (the RenoDX-style approach). Zero-effort alternative today: NVIDIA RTX HDR (NVIDIA app) on the SDR image | small | high (real HDR) |
| NVIDIA Reflex (low latency) | Streamline sl.reflex + NvLowLatencyVk.dll (already in <work dir>\sdk\sl); markers around the game's frame; with our frame lag / async worker | 0 | medium |
| FOV slider | the projection is in the scene cbuf (cot(fov/2) = 2.4142 = 45 deg); find the game's FOV value in code / patch the projection build | 0 | medium |
| Ultrawide / any aspect | runtime/nvn/widescreen code exists (from LASRecomp): check how far it works for XCDE (HUD placement) | small | medium |
| Draw distance / LOD / foliage distance | the game's LOD selection (code / map data): find the distance tables, scale them | CPU + GPU, can be large | high (research) |
| Texture quality | no better source data; HD texture packs through the new mods/ folder (community upscaled packs for XCDE exist on emulators) | VRAM | low (mods exist) |
| MSAA | not with a deferred G-buffer | - | no |
| Frame rate / V-Sync / DLSS / FSR / FG / DOF / motion blur / SMAA / internal resolution | done | | |

## 4. Proposed menu (modern-PC style), and what each maps to
- **Display:** resolution / window, fullscreen, V-Sync, frame rate limit, HDR (later), brightness (gamma), FOV.
- **Upscaling / AA:** internal resolution, DLSS / FSR 3.1 / DLAA / FSR native AA (feed the game's jitter + velocity),
  game TMAA (sharpened) / SMAA / off, sharpening slider, frame generation, Reflex.
- **Quality:** texture filtering (aniso 1-16x), texture LOD bias, shadow quality (map size 1x / 2x / 4x + shadowHalf
  off), effects resolution (TransReduction), ambient occlusion (off / TSSAO / +SSAO), reflections (SSR on/off), draw
  distance (after research), dynamic resolution (red_Auto) off.
- **Post-processing:** motion blur, depth of field, bloom, god rays / light shafts, lens flares, cloud shadows, fur blur,
  colour grading (LUT).
- **Presets:** Switch (as shipped), High, Ultra, plus a "low-end" preset for the 3200G (shadows 1x, TSSAO off,
  effects half, aniso 4x).

## 5. Suggested order (cheapest win first) and how to verify
1. Aniso 16x + LOD bias option (one sampler change; A/B captures of distant ground at 4K).
2. lib_nx toggles in the launcher / F1 menu: shadowHalf, TransReduction, red_Auto, ssr, tssao / ssao, lensFlare,
   godray, bloom, shadowCloud (each: capture A/B, GPU time with LARECOMP_GPUPROF_AT, check nothing breaks in a battle
   and a cutscene). Note: lib_nx.ini is read at boot -> these apply on restart.
3. Make TMAA the default AA again but sharper (tmaaSharpness*), since TSSAO / shadow masks depend on it; or route DLSS /
   FSR to the game's jitter + gTVelocity (find the velocity target in the frame - likely the 1280x720 RG16F written
   with the TMAA inputs) - also removes the camera-only ghosting of the current DLSS / FSR.
4. Shadow map scaling.
5. Reflex, FOV, sharpening slider.
6. Research: draw distance / LOD tables; HDR output.
