# Cross-Origin iFrame Popups

## Problem

Many e-commerce sites load marketing popups (newsletter signups, discount offers, etc.) via third-party services like Attentive, Klaviyo, etc. These popups are rendered inside **cross-origin iframes** — essentially a separate website embedded on top of the main page.

The browser-use agent cannot reliably dismiss these popups because:

1. **No DOM index.** browser-use builds an interactive element list by traversing the page's DOM. It cannot traverse into a cross-origin iframe due to the browser's same-origin security policy. The popup's close button simply doesn't appear in the agent's element list.

2. **No JS access.** `evaluate` calls that attempt to find/click elements inside the iframe are blocked by the same-origin policy. The agent tried this multiple times — always fails.

3. **Coordinate clicking is unreliable.** The agent can see the X button in the screenshot, but without an element index to snap to, it's guessing pixel coordinates from an image. It consistently misses.

## Observed Behavior

- Tested on `reebok.com` with an Attentive (`#attentive_creative`) "15% OFF" popup
- Both `bu-1-0` and `bu-2-0` spent 14-30 steps trying to dismiss the popup
- Strategies attempted by the agent: index click, Escape key, JS injection, coordinate click, page reload, DOM removal — none reliably worked
- The agent eventually succeeds by either re-navigating or brute-forcing JS removal of the gallery overlay, but wastes most of its step budget

## Potential Solutions

- **Block the popup domain** at the browser level (e.g. `prohibited_domains` on `BrowserProfile`) — simple but requires knowing the domain per-site
- **System Chrome profile** (`BrowserProfile.from_system_chrome()`) — reuses existing cookies/dismissed popups from the user's real browser
- **Browser Use Cloud** — their stealth browsers may handle these automatically
- **Pre-navigation JS injection** — nuke known popup iframes before the agent starts
- **Improve coordinate click accuracy** — better screenshot-to-coordinate mapping could make this a non-issue

## Impact

This is partly a platform limitation (no DOM indices for cross-origin iframe content) and partly a model intelligence problem. Coordinate-based clicking is available as a tool, and the X button is clearly visible in the screenshot — the models just can't reliably map what they see to accurate pixel coordinates. A model with better vision-to-coordinate reasoning could solve this without any platform changes. Affects any site using third-party marketing overlays, which is a large percentage of e-commerce sites.
