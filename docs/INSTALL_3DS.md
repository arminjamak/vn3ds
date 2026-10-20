# Playing Snapshot (or any ported game) on a real 3DS

## What the 3DS needs

- Custom firmware (Luma3DS) with the **Homebrew Launcher**. Any console set
  up with <https://3ds.hacks.guide> has both.
- For sound: `sdmc:/3ds/dspfirm.cdc`. Most hacked consoles already have it.
  If yours doesn't, run the **DSP1** homebrew app once. Without it the games
  play silently.

All commands below are run from the project folder on your computer.

## Option A: through the SD card (simplest)

1. Power the 3DS off and put its SD card in your computer.
2. Run:

   ```bash
   tools/vn3ds-port examples/demo --sd /Volumes/YOUR_SD_NAME
   ```

   This converts Snapshot and copies it to `sdmc:/3ds/vn3ds/games/snapshot/`.
   It also copies the engine to `sdmc:/3ds/vn3ds.3dsx`.
3. Eject the card and put it back in the 3DS.
4. Open the Homebrew Launcher, start **vn3ds** and pick **Snapshot**.

## Option B: over Wi-Fi (no card swapping)

The 3DS and the computer must be on the same Wi-Fi.

1. **Install the engine** (first time only). On the 3DS, open the Homebrew
   Launcher and press **Y** to start the netloader. Then run:

   ```bash
   tools/vn3ds-port --install --3ds 3DS_IP
   ```

   vn3ds starts and saves itself to the SD card. The netloader screen shows
   the 3DS's IP address.
2. **Send the game.** In vn3ds, press **Y** (*Receive*). That screen shows the
   3DS's IP address. Then run:

   ```bash
   tools/vn3ds-port examples/demo --3ds 3DS_IP
   ```

   Snapshot appears in the game list when the transfer finishes. Use the same
   command later to send an updated version.

If you use the **ftpd** homebrew app instead, replace `--3ds IP` with
`--ftp IP:5000`.

## Your other ported games

These were already converted on this computer, so they are sent as they are,
without converting again:

```bash
tools/vn3ds-port "$HOME/Library/Application Support/Azahar/sdmc/3ds/vn3ds/games/eternum" --3ds 3DS_IP
```

Eternum is 2.2 GB (13,494 images and 416 animated scenes), so expect a long
transfer over Wi-Fi. It was converted without its audio to save disk space;
to get sound, convert it again from the original download without
`--no-audio` (about 1 GB more). The SD-card route is
much faster: use `--sd /Volumes/YOUR_SD_NAME` instead of `--3ds`.
The Ren'Py SDK examples are in this project's `build/` folder (it isn't
published):

```bash
tools/vn3ds-port build/the-question build/ren-py-tutorial-game --3ds 3DS_IP
```

Only copy games you own to your own console.

## Controls

| | |
|---|---|
| A / touch | advance, choose |
| D-pad / circle pad | move through choices |
| R (hold) / L | skip / auto-forward |
| Y | history (on the game list: Receive over Wi-Fi) |
| X | save |
| START | settings, including the 3D depth |
| SELECT | hide the textbox |

The 3D slider sets how deep the scenes look.
