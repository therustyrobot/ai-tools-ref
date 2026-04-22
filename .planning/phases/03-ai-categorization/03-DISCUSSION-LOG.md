# Phase 3: AI Categorization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Session:** 2026-04-22
**Areas discussed:** Hierarchical sections, Category metadata in generate.py

---

## Area: Hierarchical sections

**Q: How should subcategories appear in the HTML output?**
- Options: Nested subsections / Subcategory badge on cards / Agent's discretion
- **Selected:** Nested subsections — each top-level category section contains sub-headers for subcategories, repos grouped within them

**Q: Should the sidebar navigation show top-level categories only, or both levels?**
- Options: Top-level only / Both levels
- **Selected:** Top-level categories only — sidebar stays clean, subcategories visible when scrolling

**Q: How should subcategory sub-headers look visually?**
- Options: Same visual pattern / Visually distinct / Agent's discretion
- **Selected (freeform):** Visually distinct with contrasting color to be an obvious divider when scrolling quickly

**Q: Which color treatment for subcategory divider headers?**
- Options: Orange accent bar / Inverted navy / Agent's discretion
- **Selected:** Orange accent bar — Safety Orange (#FF5F1F) background (strong contrast, matches primary brand)

---

## Area: Category metadata in generate.py

**Q: How should category emoji/display names be stored in generate.py?**
- Options: New CATEGORY_META dict / Extend LANG_META / Agent's discretion
- **Selected:** New CATEGORY_META dict — separate from LANG_META, check CATEGORY_META first then LANG_META then fallback 📦

**Q: Should category icons use emoji, Lucide icons, or Material Icons?**
- Options: Emoji map / Lucide via CDN script / Material Icons (already loaded) / Inline SVG
- **Selected (freeform then follow-up):** "Don't use emojis, use a flat black and white icon set like Lucide icons" → resolved to Material Icons (already loaded, consistent, no new dependency)

**Q: Does the proposed Material Icons map look right?**
- Proposed map of 14 categories with icons
- **Selected:** Looks good — use these icons

---

*Discussion log generated: 2026-04-22*
