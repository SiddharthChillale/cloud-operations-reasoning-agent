# CORA Frontend Design System

This document outlines the design philosophy, technical implementation, and aesthetic guidelines for the CORA web interface.

## 1. Design Philosophy: "Modern Enterprise Luminous"
CORA's design aims for a high-end, professional platform feel. It avoids "terminal" or "hacker" aesthetics in favor of a clean, sophisticated, and reliable look similar to modern developer tools and enterprise SaaS platforms.

### Key Principles:
- **Precision**: Crisp 1px borders and defined geometric shapes.
*   **Tactility**: Subtle noise textures to add depth and a "matte" finish.
- **Responsiveness**: Snappy, fast animations (200ms) with no unnecessary delays.
- **Clarity**: High-density information with generous negative space.

## 2. Color Palette
The palette is anchored by the primary CORA green and supported by sophisticated secondary tones.

| Name | Hex / Variable | Usage |
| :--- | :--- | :--- |
| **Vibrant Green** | `#1bcc6d` | Primary Action (Buttons, active states) |
| **Deep Emerald** | `#007f3b` | Structural accents, secondary highlights |
| **Parchment Beige** | `#E5D9B6` | Warmth accents, subtle card surfaces |
| **Obsidian** | `hsl(240 10% 3.9%)` | Dark mode background |
| **Chalk** | `hsl(0 0% 100%)` | Light mode background |

### Theme Variables (HSL)
Defined in `app/globals.css`:
- `--primary`: CORA Green highlight.
- `--secondary`: Parchment/Beige highlight.
- `--accent`: Deep Emerald depth.
- `--card`: Soft Parchment tint (Light) / Matte Black (Dark).

## 3. Typography
We use a modern, geometric pairing to ensure readability and professional tone.

- **Sans-Serif (Headers & Body)**: `Plus Jakarta Sans`
  - High-end, geometric, and very legible.
  - Linked as `--font-jakarta`.
- **Monospace (Technical/Code)**: `JetBrains Mono`
  - Used for code blocks, metrics, and technical labels.
  - Linked as `--font-jetbrains-mono`.

## 4. Visual Elements & Motion

### Noise Texture
A persistent, low-opacity noise overlay is applied globally to prevent the UI from feeling "flat".
- **Implementation**: `noise-texture` class in `globals.css` using a base64 SVG fractal noise filter.
- **Opacity**: 0.03 in Light mode, 0.05 in Dark mode.

### Transitions
- **Timing**: All transitions should be exactly `200ms` with `ease-out`.
- **Hero-to-Navbar Logo**:
  - Controlled via `framer-motion` in `components/Navbar.tsx`.
  - On the Home page, the Navbar logo starts at `opacity: 0`.
  - As the Hero logo scrolls out (threshold 100px-200px), the Navbar logo fades in.

### Border & Radius
- **Borders**: Strictly `1px` width. Use `border-border/40` for subtle structural lines.
- **Rounding**: Default radius is `0.75rem` (12px) for cards and sections.

## 5. Layout Patterns

### Global Navigation
- **Home Page**: Uses the global `Navbar` with a scroll-triggered logo transition.
- **Chat Routes**: The global `Navbar` is suppressed (`null`) to allow for a full-height workspace.

### Chat Interface (`/chat`)
- **Full-Height Sidebar**: Occupies the entire vertical space (`inset-0`).
- **Chat Header**: A dedicated internal header within the chat area containing the CORA logo, name, and theme toggle.
- **Message Area**:
  - Max-width: `4xl` for messages, `3xl` for the input bar.
  - User messages: Primary green with a soft shadow and `rounded-3xl` corners.
  - Agent messages: Card-based with a light border, subtle shadow, and `rounded-3xl` corners.
- **Floating Input Bar**: A floating, `backdrop-blur` enabled form with `2xl` rounding and `2xl` shadow depth.

### Bento Grid (Advantages)
Used for the "Key Advantages" section to present multi-faceted information in a structured, visual way. Uses 1px bordered cards with subtle hover shifts.

### The CORA Loop (Workflow)
A 6-step horizontal flow visualizing the reasoning process. 
- **Steps**: Query → Reason → Plan → Execute → Debug → Response.
- **Style**: High-contrast icons in 2x2 or row layouts.

## 6. Technical Stack
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Motion**: Framer Motion
- **Icons**: Lucide React
- **Themes**: next-themes
