# brightness_check decisions

Decisions that only affect the `brightness_check` feature. Entry format and rules:
[docs/decisions/README.md](../../../docs/decisions/README.md).

<!-- Log this feature's decisions here, newest last, starting at D1. -->

---

# Examples

> [!NOTE]
> **Examples from the template.** `brightness_check` is the template's example feature; this file
> is deleted together with it.

## D1: Mean over all pixel values instead of luminance

- **Date:** 2026-10-15
- **Status:** Accepted
- **Context:** The check needs one brightness value per image, for grayscale and color input.
- **Decision:** Use the mean of all pixel values (all channels), scaled to 0..1, rather than a
  weighted luminance (e.g. Rec. 709 `0.2126 R + 0.7152 G + 0.0722 B`).
- **Consequences:** Same code path for grayscale and color, no assumption about channel order
  (RGB vs BGR). Saturated colors are rated differently from how bright they look to a person;
  switch to luminance if that matters.
