# Destiny General Trading LLC website

An enquiry-based, bilingual (English and Arabic) static furniture catalogue. The current products and images are **provisional samples** awaiting the client's confirmed catalogue. There is no cart, checkout, server, or database. Enquiry forms open a prepared WhatsApp message.

## Deploy on Vercel

The finished website is in `dist/`. The root `vercel.json` tells Vercel to publish that directory; no build command or environment variables are needed.

1. Extract the archive and open a terminal in this folder.
2. Sign in securely with `npx vercel login` (or use an existing Vercel CLI installation).
3. Run `npx vercel` to link/create the project and inspect a preview deployment.
4. Run `npx vercel --prod` to publish to the production URL.

Alternatively, push this folder to a Git repository and import it at Vercel. Select **Other** for the framework, leave the build command empty, and use `dist` as the output directory. The included `vercel.json` also sets the output directory.

## Editing products

Edit `catalog/products.json`, then run `python3 scripts/build_catalog.py` to regenerate catalogue pages in `dist/`. Commit the regenerated files when using Git-based deployment. The four primary site pages are `dist/index.html`, `dist/about.html`, `dist/products.html` (generated), and `dist/contact.html`.

Before a client launch, replace the provisional products/images and `abc@gmail.com` with confirmed content, and verify that the configured WhatsApp number is the client's intended contact.
