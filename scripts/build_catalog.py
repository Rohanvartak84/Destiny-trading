"""Generate static, bilingual catalogue pages from catalog/products.json."""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = json.loads((ROOT / "catalog/products.json").read_text())
CATEGORIES = {item["slug"]: item for item in DATA["categories"]}
PRODUCTS = DATA["products"]
TEMPLATE = (DIST / "about.html").read_text()
HEADER = TEMPLATE[:TEMPLATE.index("  <main>")]
FOOTER = TEMPLATE[TEMPLATE.index('  <footer class="site-footer">'):]
FOOTER = FOOTER.replace('<script src="./about.js" defer></script>', '<script src="./catalog.js" defer></script>')


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def localized(tag: str, value: dict, **attrs: str) -> str:
    attributes = " ".join(f'{key.removesuffix("_").replace("_", "-")}="{esc(val)}"' for key, val in attrs.items())
    return f'<{tag} data-en="{esc(value["en"])}" data-ar="{esc(value["ar"])}" {attributes}>{esc(value["en"])}</{tag}>'


def image(image_name: str, alt: dict, *, kind: str, eager: bool = False) -> str:
    base = image_name.removesuffix(".webp")
    if base.startswith("product-"):
        original_width,scaled_height=900,675
        srcset=f'./{base}-480.webp 480w, ./{base}.webp 900w'
        src=f'./{base}.webp'
    else:
        original_width = 1536 if base in ("category-office", "category-custom") else 1448
        scaled_height = 600 if original_width == 1536 else 675
        srcset = f'./{base}-480.webp 480w, ./{base}-900.webp 900w, ./{base}.webp {original_width}w'
        src=f'./{base}-900.webp'
    sizes = "(min-width: 1100px) 25vw, (min-width: 690px) 50vw, 100vw" if kind == "card" else "(min-width: 900px) 54vw, 100vw"
    priority = 'fetchpriority="high" loading="eager"' if eager else 'loading="lazy"'
    return (f'<img src="{src}" srcset="{srcset}" sizes="{sizes}" '
            f'alt="{esc(alt["en"])}" data-alt-en="{esc(alt["en"])}" data-alt-ar="{esc(alt["ar"])}" '
            f'width="900" height="{scaled_height}" {priority} decoding="async">')


def product_card(product: dict, *, eager: bool = False, hidden: bool = False) -> str:
    category = CATEGORIES[product["category"]]
    title = localized("h3", product["name"])
    description = localized("p", product["description"])
    link = f'./product-{product["slug"]}.html'
    search_en=f'{product["name"]["en"]} {product["description"]["en"]} {product["id"]}'
    search_ar=f'{product["name"]["ar"]} {product["description"]["ar"]} {product["id"]}'
    return (f'<article class="catalog-product-card"{" hidden" if hidden else ""} data-card '
            f'data-search-en="{esc(search_en)}" data-search-ar="{esc(search_ar)}"><a class="catalog-product-image" href="{link}" '
            f'aria-label="View {esc(product["name"]["en"])} details" '
            f'data-aria-en="View {esc(product["name"]["en"])} details" '
            f'data-aria-ar="عرض تفاصيل {esc(product["name"]["ar"])}">'
            + image(product["image"], product["alt"], kind="card", eager=eager)
            + '</a><div class="catalog-product-copy">'
            + localized("span", category["name"], class_="catalog-product-category")
            + f'{title}{description}<a class="catalog-detail-link" href="{link}" '
            + f'data-en="View Details" data-ar="عرض التفاصيل">View Details <span aria-hidden="true">↗</span></a>'
            + '</div></article>')


def product_grid(products: list[dict], *, eager_first: bool = False) -> str:
    cards = ''.join(product_card(p, eager=eager_first and i == 0, hidden=i >= 8)
                    for i, p in enumerate(products))
    more = ('<button class="catalog-load-more" type="button" data-load-more data-en="Load More" '
            'data-ar="عرض المزيد">Load More</button>') if len(products) > 8 else ''
    return f'<div class="catalog-product-grid" data-catalog-grid>{cards}</div>{more}'


def related_products(product: dict, limit: int = 3) -> list[dict]:
    same=[p for p in PRODUCTS if p['id'] != product['id'] and p['category'] == product['category']]
    other=[p for p in PRODUCTS if p['id'] != product['id'] and p['category'] != product['category']]
    return (same+other)[:limit]


def sidebar(current: str = "", *, product: dict | None = None) -> str:
    heading={"en": "Browse furniture" if product else "Filter products",
             "ar": "تصفح الأثاث" if product else "تصفية المنتجات"}
    all_link = ('<a href="./products.html" ' + ('aria-current="page" ' if not current and not product else '')
                + f'><span data-en="All Products" data-ar="كل المنتجات">All Products</span><span>{len(PRODUCTS)}</span></a>')
    links = ''.join(
        f'<a href="./category-{c["slug"]}.html" '
        + ('aria-current="page" ' if current == c["slug"] else '')
        + '>'
        + localized('span', c['name'])
        + f'<span>{sum(p["category"] == c["slug"] for p in PRODUCTS)}</span></a>'
        for c in DATA['categories']
    )
    search = ('<div class="catalog-filter-search"><label for="catalog-search" data-en="Search products" '
              'data-ar="ابحث عن منتج">Search products</label><input id="catalog-search" type="search" '
              'data-search-input data-placeholder-en="Name or product ID" data-placeholder-ar="الاسم أو رقم المنتج" '
              'placeholder="Name or product ID" autocomplete="off"></div>') if not product else ''
    other = related_products(product) if product else []
    more = ('<div class="catalog-aside-more"><h3 data-en="More products" data-ar="منتجات أخرى">More products</h3>'
            + ''.join(f'<a href="./product-{p["slug"]}.html"><img src="./{p["image"].removesuffix(".webp")}-480.webp" '
                      f'alt="" width="64" height="64" loading="lazy">{localized("span", p["name"])}</a>' for p in other)
            + '</div>') if other else ''
    return ('<aside class="catalog-aside"><button class="catalog-aside-toggle" type="button" aria-expanded="false" '
            'aria-controls="catalog-aside-content" data-aside-toggle>'
            + localized('span', heading) + '<span aria-hidden="true">⌄</span></button>'
            + '<div class="catalog-aside-content" id="catalog-aside-content">'
            + localized('h2', heading) + search
            + '<nav class="catalog-filter-links" aria-label="Furniture categories" '
            'data-aria-en="Furniture categories" data-aria-ar="فئات الأثاث">'
            + all_link + links + '</nav>' + more + '</div></aside>')


def page(main: str, *, title: dict, description: dict, active: bool = True, product: dict | None = None) -> str:
    top = HEADER.replace('<title>About Destiny General Trading LLC | Furniture Supply from Dubai</title>',
                         f'<title>{esc(title["en"])}</title>')
    top = top.replace('Learn about Destiny General Trading LLC, a Dubai-based supplier of indoor, outdoor, office and custom furniture for international buyers.', esc(description["en"]))
    top = top.replace('href="./about.html" aria-current="page"', 'href="./about.html"')
    top = top.replace('href="./index.html#products"', 'href="./products.html"')
    top = top.replace('href="./contact.html" data-i18n="quote"', 'href="./contact.html" data-i18n="quote"')
    if active:
        top = top.replace('href="./products.html" data-i18n="products"', 'href="./products.html" aria-current="page" data-i18n="products"')
    top = top.replace('<body>', f'<body data-page-title-en="{esc(title["en"])}" data-page-title-ar="{esc(title["ar"])}" data-page-description-en="{esc(description["en"])}" data-page-description-ar="{esc(description["ar"])}"'
                      + (f' data-product-name-en="{esc(product["name"]["en"])}" data-product-name-ar="{esc(product["name"]["ar"])}" data-product-id="{esc(product["id"])}"' if product else '') + '>')
    bottom = FOOTER.replace('href="./index.html#products"', 'href="./products.html"')
    return top + f'  <main>{main}</main>\n' + bottom


def sample_note() -> str:
    return '<p class="catalog-sample-note" data-en="Illustrative sample content · Products and specifications await client confirmation." data-ar="محتوى توضيحي مؤقت · المنتجات والمواصفات بانتظار تأكيد العميل.">Illustrative sample content · Products and specifications await client confirmation.</p>'


def build_overview() -> None:
    title = {"en": "Furniture Products | Destiny General Trading LLC", "ar": "منتجات الأثاث | ديستني للتجارة العامة"}
    desc = {"en": "Explore illustrative indoor, outdoor, office and custom furniture categories at Destiny General Trading LLC. Enquire about confirmed options and quotations.",
            "ar": "تصفح فئات الأثاث الداخلي والخارجي والمكتبي والمخصص لدى ديستني للتجارة العامة، واستفسر عن الخيارات المتاحة وعروض الأسعار."}
    main = ('<section class="catalog-page catalog-shell"><div class="catalog-layout">'
            + sidebar() + '<div class="catalog-content"><div class="catalog-page-heading">'
            + '<p class="collections-kicker" data-en="Furniture catalogue" data-ar="كتالوج الأثاث">Furniture catalogue</p>'
            + '<h1 data-en="All Products" data-ar="كل المنتجات">All Products</h1>'
            + sample_note() + f'</div><p class="catalog-results-count" data-results-count>{len(PRODUCTS)} products</p>'
            + product_grid(PRODUCTS, eager_first=True)
            + '<p class="catalog-empty" hidden data-empty data-en="No products match your search." data-ar="لا توجد منتجات تطابق بحثك.">No products match your search.</p>'
            + '</div></div></section>')
    (DIST / "products.html").write_text(page(main, title=title, description=desc))


def build_category(category: dict) -> None:
    products = [p for p in PRODUCTS if p["category"] == category["slug"]]
    title = {lang: f'{category["name"][lang]} | Destiny General Trading LLC' for lang in ("en", "ar")}
    desc = {"en": f'Browse illustrative {category["name"]["en"].lower()} examples and enquire with Destiny General Trading LLC in Dubai.',
            "ar": f'تصفح أمثلة توضيحية من {category["name"]["ar"]} واستفسر من ديستني للتجارة العامة في دبي.'}
    main = ('<section class="catalog-page catalog-shell"><div class="catalog-layout">'
            + sidebar(category["slug"]) + '<div class="catalog-content"><div class="catalog-page-heading">'
            + '<p class="catalog-breadcrumb"><a href="./products.html" data-en="Products" data-ar="المنتجات">Products</a><span aria-hidden="true"> / </span>'
            + localized("span", category["name"]) + '</p>'
            + localized("h1", category["name"]) + localized("p", category["intro"], class_="catalog-intro-text")
            + sample_note() + f'</div><p class="catalog-results-count" data-results-count>{len(products)} {"product" if len(products)==1 else "products"}</p>'
            + product_grid(products, eager_first=True)
            + '<p class="catalog-empty" hidden data-empty data-en="No products match your search." data-ar="لا توجد منتجات تطابق بحثك.">No products match your search.</p>'
            + '</div></div></section>')
    (DIST / f'category-{category["slug"]}.html').write_text(page(main, title=title, description=desc))


def build_product(product: dict) -> None:
    category = CATEGORIES[product["category"]]
    title = {lang: f'{product["name"][lang]} | Destiny General Trading LLC' for lang in ("en", "ar")}
    desc = {"en": f'Illustrative {product["name"]["en"].lower()} example. Ask Destiny General Trading LLC about confirmed furniture options and a tailored quotation.',
            "ar": f'مثال توضيحي على {product["name"]["ar"]}. استفسر من ديستني للتجارة العامة عن الخيارات المؤكدة وعرض سعر مناسب.'}
    quote = './contact.html?' + urlencode({"product": product["name"]["en"], "productAr": product["name"]["ar"], "id": product["id"]}) + '#contact-form'
    whatsapp = 'https://wa.me/918140840069?' + urlencode({"text": f'Hello, I would like to enquire about {product["name"]["en"]} (ID: {product["id"]}). Please share the available options.'})
    related = related_products(product)
    specs = product["specifications"]
    if specs:
        spec_content = '<dl class="catalog-spec-list">' + ''.join(
            f'<div><dt data-en="{esc(item["label"]["en"])}" data-ar="{esc(item["label"]["ar"])}">{esc(item["label"]["en"])}</dt>'
            f'<dd data-en="{esc(item["value"]["en"])}" data-ar="{esc(item["value"]["ar"])}">{esc(item["value"]["en"])}</dd></div>'
            for item in specs
        ) + '</dl>'
    else:
        spec_content = '<p data-en="Materials, dimensions, finishes and customisation details will be added after the client confirms this product." data-ar="ستُضاف تفاصيل المواد والمقاسات والتشطيبات والتخصيص بعد تأكيد العميل لهذا المنتج.">Materials, dimensions, finishes and customisation details will be added after the client confirms this product.</p>'
    main = ('<section class="catalog-page catalog-shell"><div class="catalog-layout catalog-layout-detail">'
            + sidebar(category["slug"],product=product) + '<div class="catalog-content"><div class="catalog-detail">'
            + '<p class="catalog-breadcrumb"><a href="./products.html" data-en="Products" data-ar="المنتجات">Products</a><span aria-hidden="true"> / </span>'
            + f'<a href="./category-{category["slug"]}.html" data-en="{esc(category["name"]["en"])}" data-ar="{esc(category["name"]["ar"])}">{esc(category["name"]["en"])}</a></p>'
            + '<div class="catalog-detail-layout"><div class="catalog-detail-head">'
            + localized("span", category["name"], class_="catalog-product-category")
            + localized("h1", product["name"])
            + f'<p class="catalog-product-id" data-en="ID: {esc(product["id"])}" data-ar="رقم المنتج: {esc(product["id"])}">ID: {esc(product["id"])}</p>'
            + sample_note()
            + f'<a class="catalog-quote-button" href="{esc(quote)}" data-en="Request a Quote" data-ar="اطلب عرض سعر">Request a Quote</a>'
            + '</div><div class="catalog-detail-image">'
            + image(product["image"], product["alt"], kind="detail", eager=True)
            + '</div><div class="catalog-detail-more">'
            + localized("p", product["description"], class_="catalog-detail-description")
            + '<section class="catalog-specifications" aria-labelledby="catalog-spec-title">'
            + '<h2 id="catalog-spec-title" data-en="Specifications" data-ar="المواصفات">Specifications</h2>'
            + spec_content + '</section>'
            + f'<a class="catalog-whatsapp-link" href="{esc(whatsapp)}" data-product-whatsapp target="_blank" rel="noopener noreferrer" data-en="Enquire on WhatsApp ↗" data-ar="استفسر عبر واتساب ↗">Enquire on WhatsApp ↗</a>'
            + '</div></div></div><section class="catalog-related" aria-labelledby="catalog-related-title">'
            + '<h2 id="catalog-related-title" data-en="Explore more examples" data-ar="استكشف أمثلة أخرى">Explore more examples</h2><div class="catalog-product-grid">'
            + ''.join(product_card(p) for p in related) + '</div></section></div></div></section>')
    (DIST / f'product-{product["slug"]}.html').write_text(page(main, title=title, description=desc, product=product))


if __name__ == "__main__":
    build_overview()
    for item in DATA["categories"]:
        build_category(item)
    for item in PRODUCTS:
        build_product(item)
