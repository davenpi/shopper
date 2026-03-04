# Shopper

Shopper is an early checkout utility. You give it a product link, it adds the
item to cart, fills in your shipping and payment info, and asks you to confirm
before placing the order. The purchase is between you and the retailer.

## How it works

Shopper uses [browser-use](https://github.com/browser-use/browser-use) to
drive a real browser through the purchase flow. The current setup uses one
agent to get the item into cart and another to fill checkout and stop before
final submit.

## Philosophy

The idea is simple: once someone clearly wants something, software should be
able to handle the annoying part between "I want this" and "I bought it."

The hard part is reliability. Real checkout flows are messy, inconsistent, and
full of edge cases. Shopper is still figuring that part out.

## Usage

```bash
shop <product-url> [--size SIZE] [--color COLOR] [--prefs "..."]
```

Sensitive data (shipping address, payment info) is loaded from environment
variables. See `.env.example` for the full list.

## Status

Early development. The basic flow works, but reliability across real retailer
sites is still a work in progress.
