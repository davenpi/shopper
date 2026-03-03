# Shopper

Shopper is a checkout agent. You give it a product link, it adds the item to
cart, fills in your shipping and payment info, and asks you to confirm before
placing the order. The purchase is between you and the retailer — Shopper just
gets you through checkout faster.

## How it works

Shopper uses [browser-use](https://github.com/browser-use/browser-use) to
drive a real browser. A shopping agent navigates to the product page, selects
size/color, and adds to cart. A checkout agent fills in your saved details
using browser-use's sensitive data injection, so the LLM never sees your card
number or address. You confirm, and the order is placed.

## Philosophy

The product does one thing: take a link and turn it into a purchase. If that
works every time, everything else follows. If it doesn't, nothing else
matters.

So the priority is reliability across retailers, not breadth of
features. Be a vending machine before trying to be a concierge. A vending
machine does one thing and it always works. Nobody is impressed by one, but
nobody is anxious about using one either. That trust is what earns the right
to do more later.

## Usage

```
shopper <product-url> [--size SIZE] [--color COLOR] [--prefs "..."]
```

Sensitive data (shipping address, payment info) is loaded from environment
variables. See `.env.example` for the full list.

## Status

Early development. The two-agent pipeline (shopping + checkout) works for
basic flows. Active work is focused on making it reliable — handling iframe
popups, size selection grids, and cart verification across different retailer
sites.
