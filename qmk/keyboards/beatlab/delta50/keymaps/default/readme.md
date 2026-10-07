# Authored default keymap

The base follows the recorded layer-0 labels. Higher layers are new; none are claimed as vendor defaults. `via` includes this file to keep its initial mappings identical.

- The top-left detached key toggles layer 2. On layer 2 it retains that binding, so a second press exits it.
- Tab taps Tab and holds left Ctrl. The tapping term is 200 ms; completing another key's tap during the hold selects Ctrl through permissive hold.
- The key to the right of right Shift and the penultimate bottom-row key hold layer 1.
- The bottom-right key holds layer 3. Upper layers keep these layer keys transparent.
- Both spacebars remain Space. The bottom modifiers are left Alt and left GUI.

| Physical base positions | NAV (layer 1) | NUM (layer 2) | FN (layer 3) |
| --- | --- | --- | --- |
| Q W E R T Y U I O P | 1 2 3 4 5 6 7 8 9 0 | 1 2 3 4 5 6 7 8 9 0 | F1 F2 F3 F4 F5 F6 F7 F8 F9 F10 |
| `[ ]` | Minus, equals | Minus, equals | F11, F12 |
| Esc, Backspace | Grave, Delete | Base | Base |
| A S D F | Home, Page Down, Page Up, End | Base | RGB toggle, next mode, hue up, saturation up |
| G | Base | Base | RGB brightness up |
| H J K L | Left, Down, Up, Right | Base | Previous track, volume down, volume up, next track |
| Semicolon, Quote | Base, backslash | Base, backslash | Play/pause, mute |
| X C V B | Base | Base | Previous RGB mode, hue down, saturation down, brightness down |

All other positions are transparent above the base. Shift with the number layer supplies US ANSI symbols. Lighting actions do nothing when RGBLight is disabled. For static builds, edit `keymap.c` and rebuild; for VIA builds, device-stored mappings supersede compiled defaults while the stored keymap remains valid.
